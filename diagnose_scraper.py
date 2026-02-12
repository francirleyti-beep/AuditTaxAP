import sys
import os
import io

# Redireciona stdout para arquivo para garantir captura
log_file = open("scraper_diag.txt", "w", encoding="utf-8")
sys.stdout = log_file
sys.stderr = log_file

sys.path.append(os.getcwd())

from src.infrastructure.sefaz_scraper import SefazScraper
from bs4 import BeautifulSoup

try:
    path = r"c:\Projetos\AuditTaxAP\tests\samples\52260277595395006269550050000238801206971225\SEFAZ-AP_MATHEUS.html"
    
    print(f"Lendo arquivo: {path}")
    with open(path, "r", encoding="windows-1252") as f:
        html = f.read()

    print(f"Tamanho HTML: {len(html)} chars")
    
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    print(f"Total tabelas encontradas: {len(tables)}")
    
    for i, tbl in enumerate(tables):
        txt = tbl.get_text(" ", strip=True).upper()
        if "OPERACAO" in txt and "CFOP" in txt:
            print(f"--- Tabela Pre-Scan {i} ---")
            rows = tbl.find_all("tr")
            print(f"Linhas: {len(rows)}")
            for r_idx, row in enumerate(rows):
                cols = row.find_all("td")
                col_texts = [c.get_text(strip=True) for c in cols]
                print(f"  R{r_idx}: {col_texts}")

    print("\n--- Executando Scraper Real ---")
    scraper = SefazScraper()
    items = scraper.parse_html(html)
    
    print(f"\nItens Extraídos: {len(items)}")
    for item in items:
        print(f"Item {item.item_index}: CFOP='{item.cfop}' CST='{item.cst}' (Len CST: {len(item.cst)})")

except Exception as e:
    print(f"ERRO FATAL: {e}")
    import traceback
    traceback.print_exc()
finally:
    log_file.close()
