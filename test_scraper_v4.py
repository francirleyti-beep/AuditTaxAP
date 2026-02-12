import sys
import os

# Redirecionar saída para arquivo
log_file = open("test_scraper_v4.log", "w", encoding="utf-8")
sys.stdout = log_file
sys.stderr = log_file

# Adicionar src ao path
sys.path.insert(0, r"c:\Projetos\AuditTaxAP")

print("="*80)
print("TESTE DO SCRAPER V4 - CFOP e CST")
print("="*80)

try:
    # Importar a versão corrigida
    from bs4 import BeautifulSoup
    from decimal import Decimal
    from src.domain.dtos import FiscalItemDTO
    
    # Copiar a classe SefazScraper corrigida
    # (Como não podemos importar diretamente, vou recriar a função parse_html)
    
    path = r"c:\Projetos\AuditTaxAP\tests\samples\52260277595395006269550050000238801206971225\SEFAZ-AP_MATHEUS.html"
    
    print(f"\nLendo HTML: {path}")
    with open(path, "r", encoding="windows-1252") as f:
        html_content = f.read()
    
    print(f"Tamanho do HTML: {len(html_content)} chars\n")
    
    # Executar o parse
    soup = BeautifulSoup(html_content, "html.parser")
    items = []
    
    # ETAPA 1: CFOP
    print("ETAPA 1: Extraindo mapa de CFOP...")
    print("-" * 60)
    
    cfop_map = {}
    default_cfop = ""
    
    tables = soup.find_all("table")
    for i, tbl in enumerate(tables):
        text = tbl.get_text(" ", strip=True).upper()
        
        if "INFORMACOES DETALHADAS" in text and "OPERACAO" in text and "CFOP" in text:
            print(f"Tabela de CFOP encontrada (índice {i})!")
            
            tbody = tbl.find("tbody")
            if tbody:
                rows = tbody.find_all("tr")
            else:
                rows = tbl.find_all("tr")
            
            print(f"Processando {len(rows)} linhas...")
            
            for row in rows:
                cols = row.find_all("td")
                
                if len(cols) > 0:
                    first_col = cols[0].get_text(strip=True)
                    
                    if first_col.isdigit():
                        idx = int(first_col)
                        
                        if len(cols) > 2:
                            cfop_col = cols[2].get_text(strip=True)
                            
                            import re
                            match = re.match(r'(\d{4})', cfop_col)
                            if match:
                                cfop_code = match.group(1)
                                cfop_map[idx] = cfop_code
                                
                                if not default_cfop:
                                    default_cfop = cfop_code
                                
                                print(f"  Item {idx} -> CFOP {cfop_code}")
    
    print(f"\nMapa CFOP: {cfop_map}")
    print(f"CFOP Default: {default_cfop}\n")
    
    # ETAPA 2: Dados dos itens
    print("ETAPA 2: Extraindo dados dos blocos H2...")
    print("-" * 60)
    
    h2_headers = soup.find_all("h2", string=lambda t: t and t.strip().startswith("ITEM:"))
    print(f"Encontrados {len(h2_headers)} blocos H2\n")
    
    for h2 in h2_headers:
        # Extrair índice
        h2_text = h2.get_text(strip=True).replace("ITEM:", "")
        if ":" in h2_text or " " in h2_text:
            h2_text = h2_text.split(":")[0].split(" ")[0]
        
        item_idx = int(h2_text.strip()) if h2_text.strip().isdigit() else 0
        
        print(f"\nItem {item_idx}:")
        print(f"  H2 Text: {h2.get_text(strip=True)}")
        
        # Navegar para a linha
        td_item = h2.find_parent("td")
        if not td_item:
            print(f"  ERRO: TD pai não encontrado")
            continue
        
        row1 = td_item.find_parent("tr")
        if not row1:
            print(f"  ERRO: TR pai não encontrado")
            continue
        
        # Extrair dados
        cols = row1.find_all("td")
        data_map = {}
        
        for col in cols:
            h5_labels = col.find_all("h5")
            
            if h5_labels:
                for h5 in h5_labels:
                    label = h5.get_text(strip=True).upper()
                    
                    full_text = col.get_text(" ", strip=True)
                    clean_text = full_text
                    for h5_temp in h5_labels:
                        clean_text = clean_text.replace(h5_temp.get_text(strip=True), "", 1)
                    
                    clean_text = " ".join(clean_text.split())
                    
                    if label not in data_map:
                        data_map[label] = clean_text
        
        # CST
        cst_raw = data_map.get("CST", "").strip()
        import re
        cst_match = re.match(r'(\d+)', cst_raw)
        cst = cst_match.group(1) if cst_match else ""
        
        print(f"  CST Raw: '{cst_raw}'")
        print(f"  CST Extraído: '{cst}' (len={len(cst)})")
        
        # CFOP
        cfop = cfop_map.get(item_idx, default_cfop if default_cfop else "")
        print(f"  CFOP: '{cfop}'")
        
        # NCM e CEST
        ncm = data_map.get("NCM", "").strip()
        cest = data_map.get("CEST", "").strip()
        print(f"  NCM: '{ncm}'")
        print(f"  CEST: '{cest}'")
    
    print("\n" + "="*80)
    print("TESTE CONCLUÍDO")
    print("="*80)

except Exception as e:
    print(f"\nERRO FATAL: {e}")
    import traceback
    traceback.print_exc()

finally:
    log_file.close()
    
print("Log salvo em test_scraper_v4.log")
