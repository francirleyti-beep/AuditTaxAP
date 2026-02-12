# src/infrastructure/sefaz/scraper_refatorado.py
"""
Scraper SEFAZ refatorado em classes menores e mais focadas.
Cada classe tem uma responsabilidade única (Single Responsibility Principle).
"""

import re
import logging
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from src.domain.dtos import FiscalItemDTO


# =============================================================================
# GERENCIADOR DO SELENIUM
# =============================================================================

class SeleniumDriverManager:
    """
    Gerencia o ciclo de vida do WebDriver Selenium.
    
    Responsabilidades:
    - Inicializar driver
    - Abrir SEFAZ
    - Aguardar carregamento
    - Extrair HTML
    - Fechar driver
    """
    
    URL_SEFAZ = "http://www.sefaz.ap.gov.br/EMISSAO/memorial.php"
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.logger = logging.getLogger(__name__)
    
    def __enter__(self):
        """Context manager: abre driver."""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: fecha driver."""
        self.close()
    
    def open(self):
        """Inicializa e abre o WebDriver."""
        options = Options()
        
        if self.headless:
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
        
        self.logger.info("Inicializando WebDriver...")
        self.driver = webdriver.Chrome(options=options)
        self.driver.get(self.URL_SEFAZ)
        self.logger.info(f"Acessado: {self.URL_SEFAZ}")
    
    def wait_for_manual_input(self):
        """Aguarda input manual do usuário (captcha, etc)."""
        print("\n>>> AÇÃO MANUAL NECESSÁRIA <<<")
        print("1. Preencha o Captcha")
        print("2. Clique em Consultar")
        print("3. Aguarde a tabela de resultados aparecer")
        input("\nPressione ENTER quando a tabela estiver visível...")
    
    def get_page_source(self) -> str:
        """
        Retorna HTML da página atual.
        
        Returns:
            HTML completo da página
        """
        if not self.driver:
            raise RuntimeError("Driver não inicializado")
        
        html = self.driver.page_source
        self.logger.info(f"HTML capturado: {len(html)} chars")
        return html
    
    def close(self):
        """Fecha o WebDriver."""
        if self.driver:
            self.logger.info("Fechando WebDriver...")
            self.driver.quit()
            self.driver = None


# =============================================================================
# EXTRATOR DE CFOP
# =============================================================================

class CFOPExtractor:
    """
    Extrai mapa de CFOP da tabela "INFORMACOES DETALHADAS DA COBRANCA".
    
    Retorna um dicionário mapeando item_index -> CFOP.
    """
    
    # Regex compilado (otimização)
    CFOP_PATTERN = re.compile(r'(\d{4})')
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract(self, soup: BeautifulSoup) -> Tuple[Dict[int, str], str]:
        """
        Extrai mapa de CFOP.
        
        Args:
            soup: BeautifulSoup do HTML
            
        Returns:
            Tupla (cfop_map, default_cfop) onde:
                cfop_map: {item_index: cfop}
                default_cfop: CFOP mais comum (fallback)
        """
        cfop_map = {}
        default_cfop = ""
        
        # Procurar tabela específica
        for table in soup.find_all("table"):
            if self._is_cfop_table(table):
                self.logger.debug("Tabela de CFOP encontrada!")
                cfop_map, default_cfop = self._extract_from_table(table)
                break
        
        self.logger.info(f"CFOP extraídos: {len(cfop_map)} itens, default={default_cfop}")
        return cfop_map, default_cfop
    
    def _is_cfop_table(self, table) -> bool:
        """Verifica se é a tabela de CFOP."""
        text = table.get_text(" ", strip=True).upper()
        keywords = ["INFORMACOES DETALHADAS", "OPERACAO", "CFOP"]
        return all(kw in text for kw in keywords)
    
    def _extract_from_table(self, table) -> Tuple[Dict[int, str], str]:
        """Extrai CFOPs da tabela."""
        cfop_map = {}
        default_cfop = ""
        
        # Procurar tbody ou usar a table inteira
        tbody = table.find("tbody") or table
        rows = tbody.find_all("tr")
        
        for row in rows:
            cols = row.find_all("td")
            
            if len(cols) > 2:
                # Coluna 0: Item Index
                item_idx = self._extract_item_index(cols[0])
                
                # Coluna 2: CFOP
                cfop = self._extract_cfop_code(cols[2])
                
                if item_idx and cfop:
                    cfop_map[item_idx] = cfop
                    
                    if not default_cfop:
                        default_cfop = cfop
                    
                    self.logger.debug(f"  Item {item_idx} -> CFOP {cfop}")
        
        return cfop_map, default_cfop
    
    def _extract_item_index(self, cell) -> Optional[int]:
        """Extrai índice do item (primeira coluna)."""
        text = cell.get_text(strip=True)
        return int(text) if text.isdigit() else None
    
    def _extract_cfop_code(self, cell) -> Optional[str]:
        """Extrai código CFOP de 4 dígitos."""
        text = cell.get_text(strip=True)
        match = self.CFOP_PATTERN.match(text)
        return match.group(1) if match else None


# =============================================================================
# EXTRATOR DE ITENS (BLOCOS H2)
# =============================================================================

class ItemExtractor:
    """
    Extrai dados de itens dos blocos marcados com <h2>ITEM:X</h2>.
    
    Responsabilidades:
    - Encontrar blocos H2
    - Navegar estrutura HTML
    - Extrair dados de cada item
    - Montar FiscalItemDTO
    """
    
    # Regex compilados (otimização)
    CST_PATTERN = re.compile(r'(\d+)')
    MVA_PATTERN = re.compile(r'MVA ORIGINAL\s*([\d,]+)%')
    BC_PATTERN = re.compile(r'F\)\s*BASE.*?=\s*([\d\.,]+)')
    ALQ_PATTERN = re.compile(r'ALIQUOTA INTERNA\s*=\s*([\d,]+)%')
    MONEY_PATTERN = re.compile(r'(?:R\$\s*)?([\d\.]+,\d{2})')
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract(self, soup: BeautifulSoup, cfop_map: Dict[int, str], default_cfop: str = "") -> List[FiscalItemDTO]:
        """
        Extrai todos os itens fiscais.
        
        Args:
            soup: BeautifulSoup do HTML
            cfop_map: Mapa de CFOP por item
            default_cfop: CFOP padrão (fallback)
            
        Returns:
            Lista de FiscalItemDTO
        """
        items = []
        
        # Encontrar blocos H2
        h2_headers = soup.find_all("h2", string=lambda t: t and t.strip().startswith("ITEM:"))
        self.logger.info(f"Encontrados {len(h2_headers)} blocos de itens")
        
        for h2 in h2_headers:
            try:
                item = self._extract_single_item(h2, cfop_map, default_cfop)
                if item:
                    items.append(item)
                    self.logger.debug(f"✓ Item {item.item_index} extraído")
            except Exception as e:
                self.logger.error(f"Erro ao extrair item do bloco H2: {e}", exc_info=True)
                continue
        
        return items
    
    def _extract_single_item(self, h2, cfop_map: Dict[int, str], default_cfop: str) -> Optional[FiscalItemDTO]:
        """Extrai dados de um único item."""
        # 1. Extrair índice
        item_idx = self._extract_item_index(h2)
        if not item_idx:
            return None
        
        self.logger.debug(f"\nProcessando Item {item_idx}...")
        
        # 2. Navegar estrutura HTML
        row1 = self._find_parent_row(h2)
        if not row1:
            return None
        
        # 3. Extrair campos da linha 1
        data_map = self._extract_data_map(row1)
        
        # 4. Obter linhas seguintes
        row2, row3, row4 = self._get_sibling_rows(row1)
        
        # 5. Extrair campos individuais
        return FiscalItemDTO(
            origin="SEFAZ",
            item_index=item_idx,
            product_code=self._extract_product_code(data_map),
            ncm=data_map.get("NCM", "").strip(),
            cest=data_map.get("CEST", "").strip(),
            cfop=cfop_map.get(item_idx, default_cfop),
            cst=self._extract_cst(data_map),
            amount_total=Decimal("0.00"),  # Não extraído do memorial
            tax_base=self._extract_tax_base(row4),
            tax_rate=self._extract_tax_rate(row4),
            tax_value=self._extract_tax_value(data_map),
            mva_percent=self._extract_mva(row3),
            is_suframa_benefit=self._detect_suframa(row4)
        )
    
    # -------------------------------------------------------------------------
    # Navegação HTML
    # -------------------------------------------------------------------------
    
    def _extract_item_index(self, h2) -> Optional[int]:
        """Extrai índice do item do H2."""
        h2_text = h2.get_text(strip=True).replace("ITEM:", "")
        
        # Remover texto adicional após número
        if ":" in h2_text or " " in h2_text:
            h2_text = h2_text.split(":")[0].split(" ")[0]
        
        return int(h2_text.strip()) if h2_text.strip().isdigit() else None
    
    def _find_parent_row(self, h2) -> Optional:
        """Encontra a TR pai do H2."""
        td_item = h2.find_parent("td")
        if not td_item:
            self.logger.warning("TD pai não encontrado")
            return None
        
        row1 = td_item.find_parent("tr")
        if not row1:
            self.logger.warning("TR pai não encontrado")
            return None
        
        return row1
    
    def _get_sibling_rows(self, row1) -> Tuple[Optional, Optional, Optional]:
        """Obtém as 3 linhas seguintes."""
        row2 = row1.find_next_sibling("tr")
        row3 = row2.find_next_sibling("tr") if row2 else None
        row4 = row3.find_next_sibling("tr") if row3 else None
        return row2, row3, row4
    
    # -------------------------------------------------------------------------
    # Extração de Dados
    # -------------------------------------------------------------------------
    
    def _extract_data_map(self, row1) -> Dict[str, str]:
        """
        Extrai mapa {Label: Valor} da linha 1.
        
        Labels vêm em tags <h5>, valores são o texto restante da célula.
        """
        data_map = {}
        cols = row1.find_all("td")
        
        for col in cols:
            h5_labels = col.find_all("h5")
            
            if h5_labels:
                full_text = col.get_text(" ", strip=True)
                
                # Para cada label H5
                for h5 in h5_labels:
                    label = h5.get_text(strip=True).upper()
                    
                    # Remover todos os labels do texto
                    clean_text = full_text
                    for h5_temp in h5_labels:
                        clean_text = clean_text.replace(h5_temp.get_text(strip=True), "", 1)
                    
                    clean_text = " ".join(clean_text.split())  # Normalizar espaços
                    
                    if label not in data_map:
                        data_map[label] = clean_text
        
        return data_map
    
    def _extract_product_code(self, data_map: Dict[str, str]) -> str:
        """Extrai código do produto."""
        produto = data_map.get("PRODUTO", "")
        return produto.split(" ")[0] if produto else ""
    
    def _extract_cst(self, data_map: Dict[str, str]) -> str:
        """Extrai CST (apenas dígitos)."""
        cst_raw = data_map.get("CST", "").strip()
        match = self.CST_PATTERN.match(cst_raw)
        return match.group(1) if match else ""
    
    def _extract_tax_value(self, data_map: Dict[str, str]) -> Decimal:
        """Extrai valor do ICMS-ST."""
        val_raw = (data_map.get("CALCULO VALOR(SEFAZ)", "") or 
                   data_map.get("CALCULO VALOR (SEFAZ)", ""))
        return self._parse_money(val_raw)
    
    def _extract_mva(self, row3) -> Decimal:
        """Extrai MVA % da linha 3."""
        if not row3:
            return Decimal("0.00")
        
        text = row3.get_text(strip=True)
        match = self.MVA_PATTERN.search(text)
        
        if match:
            mva_str = match.group(1).replace(",", ".")
            return Decimal(mva_str)
        
        return Decimal("0.00")
    
    def _extract_tax_base(self, row4) -> Decimal:
        """Extrai base de cálculo da linha 4."""
        if not row4:
            return Decimal("0.00")
        
        text = row4.get_text(strip=True)
        match = self.BC_PATTERN.search(text)
        
        if match:
            return self._parse_money(match.group(1))
        
        return Decimal("0.00")
    
    def _extract_tax_rate(self, row4) -> Decimal:
        """Extrai alíquota interna da linha 4."""
        if not row4:
            return Decimal("0.00")
        
        text = row4.get_text(strip=True)
        match = self.ALQ_PATTERN.search(text)
        
        if match:
            alq_str = match.group(1).replace(",", ".")
            return Decimal(alq_str)
        
        return Decimal("0.00")
    
    def _detect_suframa(self, row4) -> bool:
        """Detecta se item tem benefício SUFRAMA."""
        if not row4:
            return False
        
        text = row4.get_text(" ", strip=True).upper()
        return "DESONERACAO DA SUFRAMA" in text
    
    def _parse_money(self, text: str) -> Decimal:
        """
        Converte texto para Decimal monetário.
        
        Aceita: "R$ 1.234,56" ou "1.234,56"
        """
        if not text:
            return Decimal("0.00")
        
        match = self.MONEY_PATTERN.search(text)
        if match:
            val_str = match.group(1).replace(".", "").replace(",", ".")
            return Decimal(val_str)
        
        return Decimal("0.00")


# =============================================================================
# PARSER DE HTML (ORQUESTRADOR)
# =============================================================================

class SefazHTMLParser:
    """
    Orquestra a extração de dados do HTML.
    
    Coordena CFOPExtractor e ItemExtractor.
    """
    
    def __init__(self):
        self.cfop_extractor = CFOPExtractor()
        self.item_extractor = ItemExtractor()
        self.logger = logging.getLogger(__name__)
    
    def parse(self, html: str) -> List[FiscalItemDTO]:
        """
        Parseia HTML e retorna itens fiscais.
        
        Args:
            html: HTML completo da página SEFAZ
            
        Returns:
            Lista de FiscalItemDTO
            
        Raises:
            SefazScraperException: Se nenhum item for extraído
        """
        self.logger.info("Iniciando parse do HTML...")
        
        # Parse com BeautifulSoup (lxml é mais rápido que html.parser)
        soup = BeautifulSoup(html, "lxml")
        
        # 1. Extrair mapa de CFOP
        cfop_map, default_cfop = self.cfop_extractor.extract(soup)
        
        # 2. Extrair itens
        items = self.item_extractor.extract(soup, cfop_map, default_cfop)
        
        # 3. Validar
        if not items:
            self._save_debug_html(html)
            raise SefazScraperException("Nenhum item extraído do HTML")
        
        self.logger.info(f"✓ Parse concluído: {len(items)} itens extraídos")
        return items
    
    def _save_debug_html(self, html: str):
        """Salva HTML para debug quando falha."""
        debug_file = "debug_sefaz_error.html"
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(html)
        self.logger.error(f"HTML salvo para debug em: {debug_file}")


# =============================================================================
# SCRAPER PRINCIPAL (FACHADA)
# =============================================================================

class SefazScraper:
    """
    Fachada para scraping da SEFAZ.
    
    Coordena:
    - SeleniumDriverManager: Automação do navegador
    - SefazHTMLParser: Extração de dados do HTML
    """
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.parser = SefazHTMLParser()
        self.logger = logging.getLogger(__name__)
    
    def fetch_memorial(self, nfe_key: str) -> List[FiscalItemDTO]:
        """
        Busca memorial da SEFAZ para uma NFe.
        
        Args:
            nfe_key: Chave de acesso da NFe (44 dígitos)
            
        Returns:
            Lista de FiscalItemDTO extraídos
            
        Raises:
            SefazScraperException: Em caso de erro
        """
        self.logger.info(f"Buscando memorial SEFAZ: {nfe_key}")
        
        try:
            # Context manager garante fechamento do driver
            with SeleniumDriverManager(self.headless) as driver_mgr:
                # Aguardar input manual (captcha)
                driver_mgr.wait_for_manual_input()
                
                # Extrair HTML
                html = driver_mgr.get_page_source()
                
                # Parsear
                items = self.parser.parse(html)
                
                return items
                
        except Exception as e:
            self.logger.error(f"Erro no scraping: {e}", exc_info=True)
            raise SefazScraperException(f"Falha ao buscar memorial: {e}")


# =============================================================================
# EXCEÇÃO CUSTOMIZADA
# =============================================================================

class SefazScraperException(Exception):
    """Exceção específica do scraper SEFAZ."""
    pass


# =============================================================================
# EXEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    import logging
    
    # Configurar logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Usar scraper
    scraper = SefazScraper(headless=False)
    
    try:
        items = scraper.fetch_memorial("52260277595395006269550050000238801206971225")
        
        print(f"\n✓ Sucesso! {len(items)} itens extraídos:")
        for item in items:
            print(f"  Item {item.item_index}: CFOP={item.cfop}, CST={item.cst}, "
                  f"Valor={item.tax_value}, MVA={item.mva_percent}%")
    
    except SefazScraperException as e:
        print(f"\n✗ Erro: {e}")
