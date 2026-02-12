<<<<<<< HEAD
from typing import List, Optional
from decimal import Decimal
from src.domain.dtos import FiscalItemDTO
=======
>>>>>>> 264fb42d7e4385eadda25fd1f250ebe8d81701db
from src.infrastructure.sefaz.scraper import SefazScraper

# Mantém compatibilidade com imports antigos
__all__ = ["SefazScraper"]

# Dependências externas (simuladas se não instaladas)
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from bs4 import BeautifulSoup
except ImportError:
    print("AVISO: Selenium ou BeautifulSoup não instalados. O Scraper não funcionará.")
    webdriver = None
    BeautifulSoup = None

class SefazScraper:
    """
    Responsável pela automação do navegador e extração de dados do Memorial da SEFAZ.
    Implementa a Input Layer do SPEC.
    """
    
    URL_SEFAZ = "http://www.sefaz.ap.gov.br/EMISSAO/memorial.php" # URL Fictícia baseada no PRD

    def __init__(self, headless: bool = False):
        if not webdriver:
            raise ImportError("Selenium não instalado")
        
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        
        # Inicia o driver (assume ChromeDriver no PATH)
        self.driver = webdriver.Chrome(options=options)

    def fetch_memorial(self, nfe_key: str) -> List[FiscalItemDTO]:
        """
        Acessa o site da SEFAZ, resolve captcha (com humano) e extrai a tabela.
        Retorna lista de FiscalItemDTOs com origin='SEFAZ'.
        """
        try:
            print(f"Acessando SEFAZ para chave: {nfe_key}")
            self.driver.get(self.URL_SEFAZ)
            
            # TODO: Implementar seletores reais quando tivermos acesso ao HTML real da home
            # Por enquanto, simula espera de input manual
            print(">>> AÇÃO MANUAL NECESSÁRIA <<<")
            print("1. O navegador foi aberto.")
            print("2. Preencha o Captcha e clique em Consultar.")
            print("3. Aguarde a tabela de resultados aparecer.")
            input("Pressione ENTER aqui quando a tabela estiver visível no navegador...")
            
            # Extrai HTML da página atual
            html_content = self.driver.page_source
            return self.parse_html(html_content)
            
        except Exception as e:
            print(f"Erro no scraping: {e}")
            return []
        finally:
            # Opcional: fechar ou manter aberto para debug
            # self.driver.quit()
            pass

    def parse_html(self, html_content: str) -> List[FiscalItemDTO]:
        """
        Faz o parse do HTML da SEFAZ (Versão 4 - CFOP e CST Corrigidos).
        """
        if not BeautifulSoup:
             raise ImportError("BeautifulSoup não instalado")

        soup = BeautifulSoup(html_content, "html.parser")
        items = []
        
        # ====================================================================
        # ETAPA 1: EXTRAIR MAPA DE CFOP (da tabela "INFORMACOES DETALHADAS")
        # ====================================================================
        cfop_map = {}
        default_cfop = ""
        
        try:
            print("DEBUG: Iniciando extração de CFOP...")
            target_tables = soup.find_all("table")
            
            for tbl in target_tables:
                text = tbl.get_text(" ", strip=True).upper()
                
                # Procurar pela tabela específica que tem CFOP
                if "INFORMACOES DETALHADAS" in text and "OPERACAO" in text and "CFOP" in text:
                    print("DEBUG: Tabela de CFOP encontrada!")
                    
                    # Procurar no tbody
                    tbody = tbl.find("tbody")
                    if tbody:
                        rows = tbody.find_all("tr")
                    else:
                        # Se não houver tbody, pegar todas as tr
                        rows = tbl.find_all("tr")
                    
                    print(f"DEBUG: Processando {len(rows)} linhas da tabela CFOP")
                    
                    for row in rows:
                        cols = row.find_all("td")
                        
                        # A primeira coluna deve ser o número do item
                        if len(cols) > 0:
                            first_col_text = cols[0].get_text(strip=True)
                            
                            # Verificar se é um número (índice do item)
                            if first_col_text.isdigit():
                                idx = int(first_col_text)
                                
                                # A terceira coluna (índice 2) deve conter o CFOP
                                # Formato: "6110-VENDA DE MERCAD"
                                if len(cols) > 2:
                                    cfop_col = cols[2].get_text(strip=True)
                                    
                                    # Extrair apenas os 4 dígitos do CFOP
                                    import re
                                    cfop_text = cols[2].get_text(strip=True)
                                # Ex: "6110-VENDA..." -> Regex busca 4 digitos
                                    match = re.search(r'^(\d{4})', cfop_text)
                                    cfop_code = match.group(1) if match else cfop_text.split("-")[0].strip()
                                    cfop_map[idx] = cfop_code
                                    if not default_cfop:
                                        default_cfop = cfop_code
                                        
                                    print(f"DEBUG: Item {idx} -> CFOP {cfop_code}")
            
            print(f"DEBUG: Mapa CFOP final: {cfop_map}, Default: {default_cfop}")
            
        except Exception as e:
            print(f"ERRO ao extrair mapa CFOP: {e}")
            import traceback
            traceback.print_exc()

        # ====================================================================
        # ETAPA 2: EXTRAIR DADOS DOS BLOCOS DE ITENS (H2)
        # ====================================================================
        h2_headers = soup.find_all("h2", string=lambda t: t and t.strip().startswith("ITEM:"))
        print(f"DEBUG: Encontrados {len(h2_headers)} blocos de itens (H2)")

        for h2 in h2_headers:
            try:
                # Extrair índice do item do H2
                h2_text = h2.get_text(strip=True).replace("ITEM:", "")
                # Remover qualquer texto adicional após o número
                if ":" in h2_text or " " in h2_text:
                    h2_text = h2_text.split(":")[0].split(" ")[0]
                
                item_idx = int(h2_text.strip()) if h2_text.strip().isdigit() else 0
                print(f"\nDEBUG: ===== Processando ITEM {item_idx} =====")
                
                # Navegar: h2 -> td -> tr (Linha 1)
                td_item = h2.find_parent("td")
                if not td_item:
                    print(f"ERRO: Item {item_idx} - TD pai não encontrado")
                    continue
                
                row1 = td_item.find_parent("tr")
                if not row1:
                    print(f"ERRO: Item {item_idx} - TR pai não encontrado")
                    continue

                # ------------------------------------------------------------
                # EXTRAIR DADOS DA LINHA 1 (labels em H5)
                # ------------------------------------------------------------
                cols = row1.find_all("td")
                data_map = {}
                
                for col in cols:
                    h5_labels = col.find_all("h5")
                    
                    if h5_labels:
                        # Para cada label H5 na célula
                        for h5 in h5_labels:
                            label = h5.get_text(strip=True).upper()
                            
                            # O valor vem depois do H5, no mesmo TD
                            # Estratégia: pegar todo o texto e remover os labels
                            full_text = col.get_text(" ", strip=True)
                            
                            # Remover todos os textos de H5 desta célula
                            clean_text = full_text
                            for h5_temp in h5_labels:
                                clean_text = clean_text.replace(h5_temp.get_text(strip=True), "", 1)
                            
                            # Limpar espaços extras
                            clean_text = " ".join(clean_text.split())
                            
                            # Guardar no mapa
                            if label not in data_map:  # Evitar sobrescrever
                                data_map[label] = clean_text
                
                print(f"DEBUG: Data Map Keys: {list(data_map.keys())}")
                
                # ------------------------------------------------------------
                # EXTRAIR CAMPOS ESPECÍFICOS
                # ------------------------------------------------------------
                
                def parse_money(text):
                    """Extrai valor monetário de um texto."""
                    import re
                    if not text:
                        return Decimal("0.00")
                    # Procurar padrão: R$ 1.234,56 ou 1.234,56
                    match = re.search(r'(?:R\$\s*)?([\d\.]+,\d{2})', text)
                    if match:
                        val_str = match.group(1).replace(".", "").replace(",", ".")
                        return Decimal(val_str)
                    return Decimal("0.00")
                
                # Produto
                prod_cod = data_map.get("PRODUTO", "").split(" ")[0]
                
                # NCM
                ncm = data_map.get("NCM", "").strip()
                
                # CEST
                cest = data_map.get("CEST", "").strip()
                
                # ------------------------------------------------------------
                # CST - EXTRAÇÃO CORRIGIDA
                # ------------------------------------------------------------
                cst_raw = data_map.get("CST", "").strip()
                print(f"DEBUG: CST Raw = '{cst_raw}' (len={len(cst_raw)})")
                
                # O CST pode vir no formato "040" ou "040 ST DESTACADO R$ 0,00"
                # Precisamos extrair apenas os primeiros dígitos
                import re
                cst_match = re.match(r'(\d+)', cst_raw)
                if cst_match:
                    cst = cst_match.group(1)
                else:
                    cst = ""
                
                print(f"DEBUG: CST Extraído = '{cst}'")
                
                # ------------------------------------------------------------
                # CFOP - USAR O MAPA EXTRAÍDO
                # ------------------------------------------------------------
                cfop = cfop_map.get(item_idx, "")
                
                if not cfop and default_cfop:
                    cfop = default_cfop
                    print(f"DEBUG: Usando CFOP default: {cfop}")
                
                print(f"DEBUG: CFOP Final = '{cfop}'")
                
                # ------------------------------------------------------------
                # VALOR ICMS ST (da coluna "CALCULO VALOR(SEFAZ)")
                # ------------------------------------------------------------
                val_raw = data_map.get("CALCULO VALOR(SEFAZ)", "") or data_map.get("CALCULO VALOR (SEFAZ)", "")
                v_icms_st = parse_money(val_raw)
                print(f"DEBUG: Valor ICMS-ST = {v_icms_st}")
                
                # ------------------------------------------------------------
                # LINHAS SEGUINTES (Descrição, Classificação, Cálculo)
                # ------------------------------------------------------------
                row2 = row1.find_next_sibling("tr")
                row3 = row2.find_next_sibling("tr") if row2 else None
                row4 = row3.find_next_sibling("tr") if row3 else None
                
                # MVA (Linha 3 - Classificação)
                mva = Decimal("0.00")
                if row3:
                    text_r3 = row3.get_text(strip=True)
                    import re
                    match_mva = re.search(r'MVA ORIGINAL\s*([\d,]+)%', text_r3)
                    if match_mva:
                        mva_str = match_mva.group(1).replace(",", ".")
                        mva = Decimal(mva_str)
                        print(f"DEBUG: MVA = {mva}%")
                
                # Cálculos Detalhados (Linha 4)
                v_bc = Decimal("0.00")
                p_icms = Decimal("0.00")
                is_suframa = False
                
                if row4:
                    full_text = row4.get_text(" ", strip=True)
                    is_suframa = "DESONERACAO DA SUFRAMA" in full_text.upper()
                    
                    if is_suframa:
                        print(f"DEBUG: SUFRAMA detectado!")
                    
                    # Base de cálculo
                    match_bc = re.search(r'F\)\s*BASE.*?=\s*([\d\.,]+)', full_text)
                    if match_bc:
                        v_bc = parse_money(match_bc.group(1))
                        print(f"DEBUG: Base Cálculo = {v_bc}")
                    
                    # Alíquota interna
                    match_alq = re.search(r'ALIQUOTA INTERNA\s*=\s*([\d,]+)%', full_text)
                    if match_alq:
                        p_icms = Decimal(match_alq.group(1).replace(",", "."))
                        print(f"DEBUG: Alíquota = {p_icms}%")
                
                # ------------------------------------------------------------
                # CRIAR DTO
                # ------------------------------------------------------------
                item_dto = FiscalItemDTO(
                    origin="SEFAZ",
                    item_index=item_idx,
                    product_code=prod_cod,
                    ncm=ncm,
                    cest=cest,
                    cfop=cfop,
                    cst=cst,
                    amount_total=Decimal("0.00"),  # Não extraído do memorial
                    tax_base=v_bc,
                    tax_rate=p_icms,
                    tax_value=v_icms_st,
                    mva_percent=mva,
                    is_suframa_benefit=is_suframa
                )
                items.append(item_dto)
                
                print(f"DEBUG: Item {item_idx} adicionado com sucesso!")

            except Exception as e:
                print(f"ERRO ao processar bloco H2: {e}")
                import traceback
                traceback.print_exc()
                continue

        # ====================================================================
        # VALIDAÇÃO FINAL
        # ====================================================================
        if not items:
            print("ERRO: Nenhum item foi extraído!")
            with open("debug_sefaz_error_v4.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print("HTML salvo em debug_sefaz_error_v4.html para análise")
        else:
            print(f"\nSUCESSO: {len(items)} itens extraídos!")
            for item in items:
                print(f"  Item {item.item_index}: CFOP={item.cfop}, CST={item.cst}, Valor={item.tax_value}")

        return items