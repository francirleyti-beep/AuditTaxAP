from decimal import Decimal
from typing import List
import time
from src.domain.dtos import FiscalItemDTO

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
        Faz o parse do HTML da SEFAZ (Versão 3 - Robust H2 Search).
        """
        if not BeautifulSoup:
             raise ImportError("BeautifulSoup não instalado")

        soup = BeautifulSoup(html_content, "html.parser")
        items = []
        
        # 1. Estratégia CFOP:
        # O CFOP fica numa tabela separada "INFORMACOES DETALHADAS DA COBRANCA"
        # Vamos mapear Item Index -> CFOP
        cfop_map = {}
        default_cfop = ""
        try:
             # Busca TODAS as tabelas que tenham o header específico
             target_tables = soup.find_all("table")
             for tbl in target_tables:
                 if "OPERACAO" in tbl.get_text().upper() and "CFOP" in tbl.get_text().upper():
                     # Itera linhas do corpo
                     rows = tbl.find_all("tr")
                     for row in rows:
                         cols = row.find_all("td")
                         # A primeira coluna deve ser o numero do item
                         if cols and cols[0].get_text(strip=True).isdigit():
                             idx = int(cols[0].get_text(strip=True))
                             # A col com CFOP geralmente é a 2 (Item=0, Imposto=1, Operacao=2)
                             if len(cols) > 2:
                                cfop_text = cols[2].get_text(strip=True)
                                # Ex: "6110-VENDA..."
                                cfop_code = cfop_text.split("-")[0].strip()
                                cfop_map[idx] = cfop_code
                                if not default_cfop:
                                    default_cfop = cfop_code
             print(f"DEBUG: Mapa CFOP extraído: {cfop_map}, Default: {default_cfop}")
        except Exception as e:
            print(f"Erro ao extrair mapa CFOP: {e}")

        # 2. Estratégia Dados Detalhados (Fichas):
        h2_headers = soup.find_all("h2", string=lambda t: t and t.strip().startswith("ITEM:"))
        print(f"DEBUG: Encontrados {len(h2_headers)} cabeçalhos de ITEM.")

        for h2 in h2_headers:
            try:
                # O h2 está dentro de um td. 
                # Navegar: h2 -> td -> tr (Linha 1 do bloco)
                td_item = h2.find_parent("td")
                if not td_item: continue
                
                row1 = td_item.find_parent("tr")
                if not row1: continue

                # Extrair Índice
                h2_text = h2.get_text(strip=True).replace("ITEM:", "")
                if ":" in h2_text: 
                    h2_text = h2_text.split(":")[0] 
                item_idx = int(h2_text) if h2_text.isdigit() else 0
                
                print(f"DEBUG: Processando Item {item_idx}...")

                # Dados da Linha 1 (row1) - Extração Dinâmica via Labels
                cols = row1.find_all("td")
                
                data_map = {}
                
                # Varre todas as colunas e monta mapa {Label: Valor}
                for col in cols:
                    # Tenta achar label em h5
                    h5 = col.find("h5")
                    if h5:
                        label = h5.get_text(strip=True).upper()
                        # Remove o label do texto completo da celula para pegar o valor
                        val = col.get_text(" ", strip=True).replace(h5.get_text(strip=True), "").strip()
                        data_map[label] = val
                    else:
                        # Coluna sem label explícito (ex: Item Box, ou Valor Total se estiver sem h5)
                        # Verifica se é Valor Total (tem h2 com R$)
                        if "R$" in col.get_text():
                            data_map["VALOR_TOTAL"] = col.get_text(strip=True)

                # print(f"DEBUG Map Item {item_idx}: {data_map.keys()}")

                def parse_money(text):
                    import re
                    match = re.search(r'(?:R\$\s*)?([\d\.]+,\d{2})', text)
                    if match:
                        val_str = match.group(1).replace(".", "").replace(",", ".")
                        return Decimal(val_str)
                    return Decimal("0.00")

                # Extrair campos do mapa
                prod_cod = data_map.get("PRODUTO", "").split(" ")[0] 
                ncm = data_map.get("NCM", "")
                cest = data_map.get("CEST", "")
                
                # CST e Origem
                cst_full = data_map.get("CST", "").strip()
                cst = cst_full[:3] if len(cst_full) >= 3 else ""

                # CFOP / Operação
                # Prioridade: Mapa extraído da tabela resumo
                cfop = cfop_map.get(item_idx, "")
                if not cfop and default_cfop:
                    cfop = default_cfop # Fallback para CFOP global do grupo
                
                if not cfop:
                    # Fallback secundário: Tenta achar no data_map
                    cfop_full = data_map.get("OPERACAO", "") or data_map.get("NATUREZA", "") or data_map.get("OPERAÇÃO", "")
                    cfop = cfop_full.split(" ")[0].split("-")[0].strip() if cfop_full else ""

                # Valor ICMS ST
                val_raw = data_map.get("CALCULO VALOR(SEFAZ)", "") or data_map.get("VALOR_TOTAL", "")
                v_icms_st = parse_money(val_raw)

                # CFOP, MVA, BC, e Alíquota (Nas linhas seguintes)
                row2 = row1.find_next_sibling("tr")
                row3 = row2.find_next_sibling("tr") if row2 else None
                row4 = row3.find_next_sibling("tr") if row3 else None

                # MVA (Row 3)
                mva = Decimal("0.00")
                if row3:
                    text_r3 = row3.get_text(strip=True)
                    import re
                    match_mva = re.search(r'MVA ORIGINAL\s*([\d,]+)%', text_r3)
                    if match_mva:
                        mva = Decimal(match_mva.group(1).replace(",", "."))

                # Calculos Detelhados (Row 4)
                v_bc = Decimal("0.00")
                p_icms = Decimal("0.00")
                is_suframa = False
                
                if row4:
                    full_text = row4.get_text(" ", strip=True) 
                    is_suframa = "DESONERACAO DA SUFRAMA" in full_text.upper()
                    
                    match_bc = re.search(r'F\)\s*BASE.*?=\s*([\d\.,]+)', full_text)
                    if match_bc:
                        v_bc = parse_money(match_bc.group(1)) 

                    match_alq = re.search(r'ALIQUOTA INTERNA\s*=\s*([\d,]+)%', full_text)
                    if match_alq:
                        p_icms = Decimal(match_alq.group(1).replace(",", "."))

                print(f"DEBUG: Item {item_idx} -> CFOP:{cfop} Val:{v_icms_st} BC:{v_bc}")

                item_dto = FiscalItemDTO(
                    origin="SEFAZ",
                    item_index=item_idx,
                    product_code=prod_cod,
                    ncm=ncm,
                    cest=cest,
                    cfop=cfop, 
                    cst=cst,
                    amount_total=Decimal("0.00"), 
                    tax_base=v_bc,
                    tax_rate=p_icms,
                    tax_value=v_icms_st,
                    mva_percent=mva,
                    is_suframa_benefit=is_suframa
                )
                items.append(item_dto)

            except Exception as e:
                print(f"Erro parse item bloco h2: {e}")
                continue

        if not items:
             print("Scraper v3 falhou. Nenhum item encontrado.")
             with open("debug_sefaz_error_v3.html", "w", encoding="utf-8") as f:
                f.write(html_content)

        return items
