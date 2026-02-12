# ANÁLISE E SUGESTÕES DE MELHORIA - AuditTax AP

## RESUMO EXECUTIVO

**Pontos Fortes:**
- ✓ Separação de camadas bem definida (Domain, Core, Infrastructure, Presentation)
- ✓ Uso de DTOs para transferência de dados
- ✓ Testes unitários básicos implementados
- ✓ Uso de Decimal para valores monetários (correto!)

**Pontos Críticos a Melhorar:**
- ⚠️ Falta de tratamento robusto de erros
- ⚠️ Código monolítico no scraper (420+ linhas)
- ⚠️ Performance: leitura completa do HTML sem streaming
- ⚠️ Falta de logging estruturado
- ⚠️ Testes não cobrem casos de erro
- ⚠️ Acoplamento forte entre componentes

---

## 1. ARQUITETURA GERAL

### 1.1 Estrutura Atual
```
src/
├── domain/       # DTOs ✓
├── core/         # Lógica de negócio ✓
├── infrastructure/ # I/O ✓
└── presentation/ # Relatórios ✓
```

### 1.2 Sugestões

#### A) Adicionar Camada de Serviços
```python
# src/services/audit_service.py
class AuditService:
    """Orquestra o fluxo completo de auditoria."""
    
    def __init__(self, xml_reader, scraper, auditor, reporter):
        self.xml_reader = xml_reader
        self.scraper = scraper
        self.auditor = auditor
        self.reporter = reporter
        self.logger = logging.getLogger(__name__)
    
    def audit_nfe(self, xml_path: str, nfe_key: str = None) -> str:
        """
        Executa auditoria completa de uma NFe.
        
        Returns:
            Path do relatório gerado
        """
        try:
            # 1. Ler XML
            self.logger.info(f"Lendo XML: {xml_path}")
            key, xml_items = self.xml_reader.parse(xml_path)
            nfe_key = nfe_key or key
            
            # 2. Buscar SEFAZ
            self.logger.info(f"Buscando memorial SEFAZ: {nfe_key}")
            sefaz_items = self.scraper.fetch_memorial(nfe_key)
            
            if not sefaz_items:
                raise AuditException("Nenhum item retornado da SEFAZ")
            
            # 3. Auditar
            self.logger.info("Iniciando auditoria...")
            results = self._audit_items(xml_items, sefaz_items)
            
            # 4. Gerar relatório
            self.logger.info("Gerando relatório...")
            report_path = self.reporter.generate_excel(results)
            
            return report_path
            
        except Exception as e:
            self.logger.error(f"Erro na auditoria: {e}", exc_info=True)
            raise

    def _audit_items(self, xml_items, sefaz_items):
        """Auditoria item por item."""
        sefaz_map = {item.item_index: item for item in sefaz_items}
        results = []
        
        for xml_item in xml_items:
            sefaz_item = sefaz_map.get(xml_item.item_index)
            
            if not sefaz_item:
                self.logger.warning(f"Item {xml_item.item_index} não encontrado na SEFAZ")
                continue
            
            result = self.auditor.audit_item(xml_item, sefaz_item)
            results.append(result)
        
        return results
```

**Benefícios:**
- Lógica de orquestração separada
- Facilita testes (mock de cada componente)
- Reutilizável em diferentes contextos (CLI, API, GUI)

#### B) Adicionar Exceções Customizadas
```python
# src/domain/exceptions.py
class AuditTaxException(Exception):
    """Exceção base do sistema."""
    pass

class XMLParseException(AuditTaxException):
    """Erro ao parsear XML."""
    pass

class SefazScraperException(AuditTaxException):
    """Erro no scraping da SEFAZ."""
    pass

class AuditException(AuditTaxException):
    """Erro na auditoria."""
    pass

class ReportGenerationException(AuditTaxException):
    """Erro na geração de relatório."""
    pass
```

---

## 2. DOMAIN LAYER (DTOs)

### 2.1 Código Atual
```python
@dataclass
class FiscalItemDTO:
    origin: str
    item_index: int
    product_code: str
    # ... 9 campos mais
```

### 2.2 Sugestões

#### A) Validação de Dados
```python
from dataclasses import dataclass, field
from typing import Optional
from decimal import Decimal

@dataclass
class FiscalItemDTO:
    origin: str  # 'XML' ou 'SEFAZ'
    item_index: int
    product_code: str
    ncm: str
    cest: str
    cfop: str
    cst: str
    amount_total: Decimal
    tax_base: Decimal
    tax_rate: Decimal
    tax_value: Decimal
    mva_percent: Decimal
    is_suframa_benefit: bool
    
    def __post_init__(self):
        """Validações após inicialização."""
        # Validar origem
        if self.origin not in ['XML', 'SEFAZ']:
            raise ValueError(f"Origin inválida: {self.origin}")
        
        # Validar item_index
        if self.item_index <= 0:
            raise ValueError(f"item_index deve ser positivo: {self.item_index}")
        
        # Validar NCM (8 dígitos)
        if self.ncm and not (len(self.ncm) == 8 and self.ncm.isdigit()):
            raise ValueError(f"NCM inválido: {self.ncm}")
        
        # Validar CFOP (4 dígitos)
        if self.cfop and not (len(self.cfop) == 4 and self.cfop.isdigit()):
            raise ValueError(f"CFOP inválido: {self.cfop}")
        
        # Validar valores não negativos
        for field_name in ['amount_total', 'tax_base', 'tax_rate', 'tax_value', 'mva_percent']:
            value = getattr(self, field_name)
            if value < 0:
                raise ValueError(f"{field_name} não pode ser negativo: {value}")
    
    @property
    def is_valid(self) -> bool:
        """Verifica se o item tem dados mínimos para auditoria."""
        return bool(self.product_code and self.ncm and self.cfop and self.cst)
```

#### B) Métodos Auxiliares
```python
@dataclass
class FiscalItemDTO:
    # ... campos ...
    
    def to_dict(self) -> dict:
        """Serializa para dicionário."""
        return {
            'origin': self.origin,
            'item_index': self.item_index,
            'product_code': self.product_code,
            'ncm': self.ncm,
            'cest': self.cest,
            'cfop': self.cfop,
            'cst': self.cst,
            'amount_total': str(self.amount_total),
            'tax_base': str(self.tax_base),
            'tax_rate': str(self.tax_rate),
            'tax_value': str(self.tax_value),
            'mva_percent': str(self.mva_percent),
            'is_suframa_benefit': self.is_suframa_benefit,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FiscalItemDTO':
        """Cria instância a partir de dicionário."""
        decimal_fields = ['amount_total', 'tax_base', 'tax_rate', 'tax_value', 'mva_percent']
        
        for field in decimal_fields:
            if field in data and isinstance(data[field], str):
                data[field] = Decimal(data[field])
        
        return cls(**data)
```

---

## 3. CORE LAYER

### 3.1 Auditor (src/core/auditor.py)

#### Problema: Lógica rígida e acoplada
```python
def audit_item(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO):
    differences = []
    
    # Hardcoded checks
    self._check_equality(differences, "NCM", xml_item.ncm, sefaz_item.ncm)
    self._check_equality(differences, "CEST", xml_item.cest, sefaz_item.cest)
    # ...
```

#### Solução: Strategy Pattern + Chain of Responsibility
```python
# src/core/audit_rules.py
from abc import ABC, abstractmethod
from typing import List, Optional

class AuditRule(ABC):
    """Regra base de auditoria."""
    
    def __init__(self, tolerance: Decimal = Decimal("0.00")):
        self.tolerance = tolerance
        self.next_rule: Optional[AuditRule] = None
    
    def set_next(self, rule: 'AuditRule') -> 'AuditRule':
        """Encadeia próxima regra."""
        self.next_rule = rule
        return rule
    
    def check(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> List[AuditDifference]:
        """Executa verificação."""
        differences = self._execute(xml_item, sefaz_item)
        
        if self.next_rule:
            differences.extend(self.next_rule.check(xml_item, sefaz_item))
        
        return differences
    
    @abstractmethod
    def _execute(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> List[AuditDifference]:
        """Implementa a regra específica."""
        pass


class NCMRule(AuditRule):
    """Verifica concordância de NCM."""
    
    def _execute(self, xml_item, sefaz_item):
        if xml_item.ncm != sefaz_item.ncm:
            return [AuditDifference(
                field="NCM",
                xml_value=xml_item.ncm,
                sefaz_value=sefaz_item.ncm,
                message="Divergência de NCM"
            )]
        return []


class CFOPRule(AuditRule):
    """Verifica concordância de CFOP."""
    
    def _execute(self, xml_item, sefaz_item):
        if xml_item.cfop != sefaz_item.cfop:
            return [AuditDifference(
                field="CFOP",
                xml_value=xml_item.cfop,
                sefaz_value=sefaz_item.cfop,
                message="Divergência de CFOP"
            )]
        return []


class CSTRule(AuditRule):
    """Verifica concordância de CST (normalizado)."""
    
    def _execute(self, xml_item, sefaz_item):
        cst_xml = xml_item.cst.lstrip("0") if xml_item.cst else ""
        cst_sefaz = sefaz_item.cst.lstrip("0") if sefaz_item.cst else ""
        
        if cst_xml != cst_sefaz:
            return [AuditDifference(
                field="CST",
                xml_value=cst_xml,
                sefaz_value=cst_sefaz,
                message="Divergência de CST"
            )]
        return []


class MonetaryRule(AuditRule):
    """Verifica concordância de valores monetários."""
    
    def __init__(self, field_name: str, tolerance: Decimal = Decimal("0.05")):
        super().__init__(tolerance)
        self.field_name = field_name
    
    def _execute(self, xml_item, sefaz_item):
        val_xml = getattr(xml_item, self.field_name.lower().replace(" ", "_"))
        val_sefaz = getattr(sefaz_item, self.field_name.lower().replace(" ", "_"))
        
        delta = abs(val_xml - val_sefaz)
        
        if delta > self.tolerance:
            return [AuditDifference(
                field=self.field_name,
                xml_value=str(val_xml),
                sefaz_value=str(val_sefaz),
                message=f"Divergência de {self.field_name} (Dif: {delta})"
            )]
        return []


# src/core/auditor.py (refatorado)
class AuditEngine:
    """Motor de auditoria configurável."""
    
    def __init__(self, tolerance: Decimal = Decimal("0.05")):
        self.tolerance = tolerance
        self.calculator = TaxCalculator()
        self._build_rule_chain()
    
    def _build_rule_chain(self):
        """Constrói cadeia de regras."""
        # Regras cadastrais
        ncm = NCMRule()
        cest = CESTRule()
        cfop = CFOPRule()
        cst = CSTRule()
        
        # Regras monetárias
        tax_base = MonetaryRule("tax_base", self.tolerance)
        tax_value = MonetaryRule("tax_value", self.tolerance)
        mva = MonetaryRule("mva_percent", self.tolerance)
        
        # Encadear
        ncm.set_next(cest).set_next(cfop).set_next(cst)\
           .set_next(tax_base).set_next(tax_value).set_next(mva)
        
        self.rule_chain = ncm
    
    def audit_item(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> AuditResultDTO:
        """Executa auditoria usando cadeia de regras."""
        differences = self.rule_chain.check(xml_item, sefaz_item)
        
        return AuditResultDTO(
            item_index=xml_item.item_index,
            product_code=xml_item.product_code,
            is_compliant=(len(differences) == 0),
            differences=differences
        )
```

**Benefícios:**
- ✓ Fácil adicionar/remover regras
- ✓ Regras reutilizáveis
- ✓ Cada regra testável individualmente
- ✓ Configurável (ordem das regras, tolerâncias)

---

## 4. INFRASTRUCTURE LAYER

### 4.1 XML Reader (src/infrastructure/xml_reader.py)

#### Problema: Lógica confusa de namespace
```python
ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
if not root.tag.startswith('{http://www.portalfiscal.inf.br/nfe}'):
    ns = {}
```

#### Solução: Helper de namespace
```python
class XMLReader:
    NFE_NAMESPACE = "http://www.portalfiscal.inf.br/nfe"
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse(self, xml_path: str) -> tuple[str, list[FiscalItemDTO]]:
        """Lê arquivo XML e retorna chave NFe e itens."""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Detectar namespace
            ns = self._detect_namespace(root)
            
            # Extrair chave
            nfe_key = self._extract_nfe_key(root, ns)
            
            # Extrair itens
            items = self._extract_items(root, ns)
            
            self.logger.info(f"XML parsed: {len(items)} items, key={nfe_key}")
            
            return nfe_key, items
            
        except ET.ParseError as e:
            raise XMLParseException(f"XML inválido: {e}")
        except Exception as e:
            raise XMLParseException(f"Erro ao ler XML: {e}")
    
    def _detect_namespace(self, root) -> dict:
        """Detecta namespace do XML."""
        if root.tag.startswith(f'{{{self.NFE_NAMESPACE}}}'):
            return {'nfe': self.NFE_NAMESPACE}
        return {}
    
    def _extract_nfe_key(self, root, ns: dict) -> str:
        """Extrai chave de acesso da NFe."""
        inf_nfe = root.find(".//nfe:infNFe", ns) if ns else root.find(".//infNFe")
        
        if inf_nfe is None:
            return ""
        
        raw_id = inf_nfe.get("Id", "")
        return raw_id[3:] if raw_id.startswith("NFe") else raw_id
    
    def _extract_items(self, root, ns: dict) -> list[FiscalItemDTO]:
        """Extrai itens fiscais do XML."""
        dets = root.findall(".//nfe:det", ns) if ns else root.findall(".//det")
        items = []
        
        for det in dets:
            try:
                item = self._parse_det_item(det, ns)
                if item:
                    items.append(item)
            except Exception as e:
                self.logger.error(f"Erro ao processar item {det.get('nItem')}: {e}")
                continue
        
        return items
    
    def _parse_det_item(self, det, ns: dict) -> Optional[FiscalItemDTO]:
        """Parseia um elemento <det>."""
        # Helper para find com namespace
        def find_text(node, tag, default=""):
            found = node.find(f"nfe:{tag}", ns) if ns else node.find(tag)
            return found.text if found is not None else default
        
        # Item index
        n_item_str = det.get("nItem")
        n_item = int(n_item_str) if n_item_str and n_item_str.isdigit() else 0
        
        # Produto
        prod = det.find("nfe:prod", ns) if ns else det.find("prod")
        if prod is None:
            return None
        
        # ... resto da extração ...
        
        return FiscalItemDTO(
            origin="XML",
            item_index=n_item,
            # ... campos ...
        )
```

---

## 5. SEFAZ SCRAPER

### 5.1 Problema: Código Monolítico (420 linhas!)

#### Solução: Dividir em Classes Especializadas

```python
# src/infrastructure/sefaz/scraper.py
class SefazScraper:
    """Orquestrador principal."""
    
    def __init__(self, headless: bool = False):
        self.driver_manager = SeleniumDriverManager(headless)
        self.html_parser = SefazHTMLParser()
        self.logger = logging.getLogger(__name__)
    
    def fetch_memorial(self, nfe_key: str) -> List[FiscalItemDTO]:
        """Busca memorial na SEFAZ."""
        try:
            # 1. Abrir navegador e acessar site
            self.driver_manager.open_sefaz()
            
            # 2. Resolver captcha (manual ou automático)
            self.driver_manager.wait_for_table()
            
            # 3. Extrair HTML
            html = self.driver_manager.get_page_source()
            
            # 4. Parsear
            return self.html_parser.parse(html)
            
        finally:
            self.driver_manager.close()


# src/infrastructure/sefaz/driver_manager.py
class SeleniumDriverManager:
    """Gerencia Selenium WebDriver."""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
    
    def open_sefaz(self):
        """Abre navegador na SEFAZ."""
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.get(SefazScraper.URL_SEFAZ)
    
    def wait_for_table(self):
        """Aguarda tabela aparecer."""
        # TODO: Implementar wait com Selenium
        input("Pressione ENTER quando a tabela estiver visível...")
    
    def get_page_source(self) -> str:
        """Retorna HTML da página."""
        return self.driver.page_source
    
    def close(self):
        """Fecha navegador."""
        if self.driver:
            self.driver.quit()


# src/infrastructure/sefaz/html_parser.py
class SefazHTMLParser:
    """Parseia HTML do memorial SEFAZ."""
    
    def __init__(self):
        self.cfop_extractor = CFOPExtractor()
        self.item_extractor = ItemExtractor()
        self.logger = logging.getLogger(__name__)
    
    def parse(self, html: str) -> List[FiscalItemDTO]:
        """Extrai itens do HTML."""
        soup = BeautifulSoup(html, "html.parser")
        
        # 1. Extrair mapa de CFOP
        cfop_map = self.cfop_extractor.extract(soup)
        
        # 2. Extrair itens
        items = self.item_extractor.extract(soup, cfop_map)
        
        if not items:
            self._save_debug_html(html)
            raise SefazScraperException("Nenhum item extraído")
        
        return items
    
    def _save_debug_html(self, html: str):
        """Salva HTML para debug."""
        with open("debug_sefaz_error.html", "w", encoding="utf-8") as f:
            f.write(html)


# src/infrastructure/sefaz/cfop_extractor.py
class CFOPExtractor:
    """Extrai mapa de CFOP da tabela resumo."""
    
    def extract(self, soup: BeautifulSoup) -> dict[int, str]:
        """Retorna {item_index: cfop}."""
        cfop_map = {}
        default_cfop = ""
        
        # Procurar tabela específica
        for table in soup.find_all("table"):
            text = table.get_text(" ", strip=True).upper()
            
            if self._is_cfop_table(text):
                cfop_map, default_cfop = self._extract_from_table(table)
                break
        
        return cfop_map
    
    def _is_cfop_table(self, text: str) -> bool:
        """Verifica se é a tabela de CFOP."""
        return all(keyword in text for keyword in 
                   ["INFORMACOES DETALHADAS", "OPERACAO", "CFOP"])
    
    def _extract_from_table(self, table) -> tuple[dict, str]:
        """Extrai CFOPs da tabela."""
        cfop_map = {}
        default_cfop = ""
        
        tbody = table.find("tbody") or table
        rows = tbody.find_all("tr")
        
        for row in rows:
            cols = row.find_all("td")
            
            if len(cols) > 2:
                item_idx = self._extract_item_index(cols[0])
                cfop = self._extract_cfop_code(cols[2])
                
                if item_idx and cfop:
                    cfop_map[item_idx] = cfop
                    if not default_cfop:
                        default_cfop = cfop
        
        return cfop_map, default_cfop
    
    def _extract_item_index(self, cell) -> Optional[int]:
        """Extrai índice do item."""
        text = cell.get_text(strip=True)
        return int(text) if text.isdigit() else None
    
    def _extract_cfop_code(self, cell) -> Optional[str]:
        """Extrai código CFOP."""
        text = cell.get_text(strip=True)
        match = re.match(r'(\d{4})', text)
        return match.group(1) if match else None


# src/infrastructure/sefaz/item_extractor.py
class ItemExtractor:
    """Extrai dados de itens dos blocos H2."""
    
    def extract(self, soup: BeautifulSoup, cfop_map: dict) -> List[FiscalItemDTO]:
        """Extrai todos os itens."""
        items = []
        h2_headers = soup.find_all("h2", string=lambda t: t and t.strip().startswith("ITEM:"))
        
        for h2 in h2_headers:
            try:
                item = self._extract_item(h2, cfop_map)
                if item:
                    items.append(item)
            except Exception as e:
                self.logger.error(f"Erro ao extrair item: {e}")
                continue
        
        return items
    
    def _extract_item(self, h2, cfop_map: dict) -> Optional[FiscalItemDTO]:
        """Extrai um item individual."""
        # Extrair índice
        item_idx = self._extract_item_index(h2)
        
        # Navegar estrutura
        row1 = self._find_parent_row(h2)
        if not row1:
            return None
        
        # Extrair campos
        data_map = self._extract_data_map(row1)
        
        # Extrair linhas seguintes
        row2, row3, row4 = self._get_sibling_rows(row1)
        
        # Montar DTO
        return FiscalItemDTO(
            origin="SEFAZ",
            item_index=item_idx,
            product_code=self._extract_product_code(data_map),
            ncm=data_map.get("NCM", "").strip(),
            cest=data_map.get("CEST", "").strip(),
            cfop=cfop_map.get(item_idx, ""),
            cst=self._extract_cst(data_map),
            amount_total=Decimal("0.00"),
            tax_base=self._extract_tax_base(row4),
            tax_rate=self._extract_tax_rate(row4),
            tax_value=self._extract_tax_value(data_map),
            mva_percent=self._extract_mva(row3),
            is_suframa_benefit=self._detect_suframa(row4)
        )
    
    # ... métodos auxiliares ...
```

**Benefícios:**
- ✓ Cada classe tem responsabilidade única (SRP)
- ✓ Fácil testar cada extrator separadamente
- ✓ Código mais legível e manutenível
- ✓ Reduz acoplamento

---

## 6. PERFORMANCE

### 6.1 Otimizações Críticas

#### A) Cache de Compilação Regex
```python
# Antes (compila regex a cada item)
match = re.search(r'MVA ORIGINAL\s*([\d,]+)%', text)

# Depois (compila uma vez)
class ItemExtractor:
    MVA_PATTERN = re.compile(r'MVA ORIGINAL\s*([\d,]+)%')
    CFOP_PATTERN = re.compile(r'(\d{4})')
    CST_PATTERN = re.compile(r'(\d+)')
    BC_PATTERN = re.compile(r'F\)\s*BASE.*?=\s*([\d\.,]+)')
    MONEY_PATTERN = re.compile(r'(?:R\$\s*)?([\d\.]+,\d{2})')
    
    def _extract_mva(self, row):
        text = row.get_text(strip=True)
        match = self.MVA_PATTERN.search(text)
        return Decimal(match.group(1).replace(",", ".")) if match else Decimal("0.00")
```

#### B) Processamento Paralelo (XML com múltiplos itens)
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

class AuditEngine:
    def audit_items_parallel(self, xml_items, sefaz_map, max_workers=4):
        """Auditoria paralela de itens."""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.audit_item, xml_item, sefaz_map.get(xml_item.item_index)): xml_item
                for xml_item in xml_items
                if xml_item.item_index in sefaz_map
            }
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    xml_item = futures[future]
                    self.logger.error(f"Erro item {xml_item.item_index}: {e}")
        
        # Ordenar por índice
        return sorted(results, key=lambda r: r.item_index)
```

#### C) Lazy Loading de BeautifulSoup
```python
def parse_html(self, html: str) -> List[FiscalItemDTO]:
    """Parse com lxml (mais rápido que html.parser)."""
    soup = BeautifulSoup(html, "lxml")  # 2x-3x mais rápido!
    # ... resto do código ...
```

---

## 7. LOGGING ESTRUTURADO

### Problema: Apenas `print()`
```python
print("DEBUG: Processando item...")
```

### Solução: Logging profissional
```python
# src/utils/logging_config.py
import logging
import sys
from pathlib import Path

def setup_logging(log_level=logging.INFO, log_file=None):
    """Configura sistema de logging."""
    
    # Formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Handler arquivo (se fornecido)
    handlers = [console_handler]
    
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configurar root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers
    )
    
    # Silenciar logs verbosos de terceiros
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


# main.py
from src.utils.logging_config import setup_logging

def main():
    # Setup logging
    log_file = Path("logs") / f"audit_{datetime.now():%Y%m%d_%H%M%S}.log"
    log_file.parent.mkdir(exist_ok=True)
    setup_logging(log_level=logging.INFO, log_file=log_file)
    
    logger = logging.getLogger(__name__)
    logger.info("=== AuditTax AP - Início ===")
    
    # ... resto do código ...
```

---

## 8. TESTES

### 8.1 Problemas Atuais
- Cobertura baixa
- Não testa casos de erro
- Usa mocks inadequados

### 8.2 Sugestões

#### A) Fixtures e Parametrização
```python
# tests/conftest.py
import pytest
from decimal import Decimal
from src.domain.dtos import FiscalItemDTO

@pytest.fixture
def sample_xml_item():
    """Item fiscal do XML."""
    return FiscalItemDTO(
        origin="XML",
        item_index=1,
        product_code="PROD-001",
        ncm="22021000",
        cest="0300700",
        cfop="6110",
        cst="040",
        amount_total=Decimal("100.00"),
        tax_base=Decimal("100.00"),
        tax_rate=Decimal("18.00"),
        tax_value=Decimal("18.00"),
        mva_percent=Decimal("30.00"),
        is_suframa_benefit=False
    )

@pytest.fixture
def sample_sefaz_item():
    """Item fiscal da SEFAZ."""
    return FiscalItemDTO(
        origin="SEFAZ",
        item_index=1,
        product_code="PROD-001",
        ncm="22021000",
        cest="0300700",
        cfop="6110",
        cst="040",
        amount_total=Decimal("0.00"),
        tax_base=Decimal("100.00"),
        tax_rate=Decimal("18.00"),
        tax_value=Decimal("18.00"),
        mva_percent=Decimal("30.00"),
        is_suframa_benefit=False
    )


# tests/test_auditor.py
import pytest
from decimal import Decimal

@pytest.mark.parametrize("field,xml_val,sefaz_val,should_fail", [
    ("ncm", "12345678", "87654321", True),
    ("ncm", "12345678", "12345678", False),
    ("cfop", "6110", "5102", True),
    ("cfop", "6110", "6110", False),
])
def test_audit_field_divergence(sample_xml_item, sample_sefaz_item, field, xml_val, sefaz_val, should_fail):
    """Testa divergências em campos específicos."""
    engine = AuditEngine()
    
    # Modificar valores
    setattr(sample_xml_item, field, xml_val)
    setattr(sample_sefaz_item, field, sefaz_val)
    
    # Auditar
    result = engine.audit_item(sample_xml_item, sample_sefaz_item)
    
    # Verificar
    if should_fail:
        assert not result.is_compliant
        assert any(d.field.lower() == field for d in result.differences)
    else:
        assert result.is_compliant


def test_audit_monetary_tolerance():
    """Testa tolerância em valores monetários."""
    engine = AuditEngine(tolerance=Decimal("0.05"))
    
    xml_item = sample_xml_item()
    sefaz_item = sample_sefaz_item()
    
    # Diferença dentro da tolerância
    sefaz_item.tax_value = Decimal("18.03")  # +0.03
    result = engine.audit_item(xml_item, sefaz_item)
    assert result.is_compliant
    
    # Diferença fora da tolerância
    sefaz_item.tax_value = Decimal("18.10")  # +0.10
    result = engine.audit_item(xml_item, sefaz_item)
    assert not result.is_compliant
```

#### B) Testes de Integração
```python
# tests/integration/test_full_audit.py
def test_full_audit_flow(tmp_path):
    """Testa fluxo completo de auditoria."""
    # 1. Preparar XML de teste
    xml_file = tmp_path / "test.xml"
    xml_file.write_text(SAMPLE_XML_CONTENT)
    
    # 2. Mock SEFAZ scraper
    mock_scraper = Mock()
    mock_scraper.fetch_memorial.return_value = [sample_sefaz_item()]
    
    # 3. Executar serviço
    service = AuditService(
        xml_reader=XMLReader(),
        scraper=mock_scraper,
        auditor=AuditEngine(),
        reporter=ReportGenerator()
    )
    
    report_path = service.audit_nfe(str(xml_file))
    
    # 4. Verificar
    assert Path(report_path).exists()
    assert Path(report_path).suffix == ".csv"
```

---

## 9. CONFIGURAÇÃO

### Problema: Valores hardcoded
```python
URL_SEFAZ = "http://www.sefaz.ap.gov.br/EMISSAO/memorial.php"
tolerance = Decimal("0.05")
```

### Solução: Arquivo de configuração
```python
# config.py
from pydantic import BaseSettings
from decimal import Decimal
from typing import Optional

class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    # SEFAZ
    sefaz_url: str = "http://www.sefaz.ap.gov.br/EMISSAO/memorial.php"
    sefaz_timeout: int = 30
    selenium_headless: bool = False
    
    # Auditoria
    audit_tolerance: Decimal = Decimal("0.05")
    parallel_workers: int = 4
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Relatório
    report_format: str = "csv"  # 'csv' ou 'xlsx'
    report_directory: str = "reports"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Singleton
settings = Settings()


# .env (não commitar!)
SEFAZ_URL=http://www.sefaz.ap.gov.br/EMISSAO/memorial.php
AUDIT_TOLERANCE=0.05
LOG_LEVEL=DEBUG
SELENIUM_HEADLESS=true
```

---

## 10. CONCLUSÃO E ROADMAP

### Prioridade ALTA (Fazer AGORA)
1. ✓ Adicionar logging estruturado
2. ✓ Separar SefazScraper em classes menores
3. ✓ Implementar tratamento de exceções customizadas
4. ✓ Adicionar validação nos DTOs

### Prioridade MÉDIA (Próximas sprints)
5. ✓ Refatorar auditor com Strategy Pattern
6. ✓ Criar camada de serviços
7. ✓ Melhorar cobertura de testes
8. ✓ Adicionar configuração externa

### Prioridade BAIXA (Melhorias futuras)
9. ✓ Processamento paralelo
10. ✓ Cache de compilação regex
11. ✓ Interface gráfica (Streamlit/Tkinter)
12. ✓ API REST (FastAPI)

### Métricas Estimadas

**Antes:**
- Linhas de código: ~800
- Complexidade ciclomática: Alta (15-20 por função)
- Cobertura de testes: ~30%
- Tempo de execução: ~10s por NFe

**Depois (com refatorações):**
- Linhas de código: ~1200 (mas muito mais organizadas)
- Complexidade ciclomática: Baixa (3-5 por função)
- Cobertura de testes: ~80%
- Tempo de execução: ~6s por NFe (40% mais rápido com otimizações)

---

## APÊNDICE: Checklist de Revisão de Código

Use este checklist para futuras revisões:

### Código Limpo
- [ ] Nomes de variáveis descritivos
- [ ] Funções com responsabilidade única
- [ ] Máximo 50 linhas por função
- [ ] Sem código comentado
- [ ] Type hints em todas as funções

### Arquitetura
- [ ] Separação clara de camadas
- [ ] Baixo acoplamento
- [ ] Alta coesão
- [ ] Princípios SOLID respeitados

### Testes
- [ ] Cobertura > 80%
- [ ] Testes unitários + integração
- [ ] Casos de erro testados
- [ ] Fixtures reutilizáveis

### Performance
- [ ] Regex compilado uma vez
- [ ] Operações I/O otimizadas
- [ ] Sem operações bloqueantes
- [ ] Profiling realizado

### Segurança
- [ ] Validação de inputs
- [ ] Exceções tratadas
- [ ] Logs não expõem dados sensíveis
- [ ] Dependências atualizadas

### Documentação
- [ ] README atualizado
- [ ] Docstrings em classes/funções
- [ ] Exemplos de uso
- [ ] Guia de contribuição
