import sys
import os

# Output to absolute path file
log_path = os.path.abspath("table_dump.txt")
sys.stdout = open(log_path, "w", encoding="utf-8")
sys.stderr = sys.stdout

try:
    from bs4 import BeautifulSoup
    path = r"c:\Projetos\AuditTaxAP\tests\samples\52260277595395006269550050000238801206971225\SEFAZ-AP_MATHEUS.html"
    
    print(f"Lendo: {path}")
    with open(path, "r", encoding="windows-1252") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    print(f"Total Tables: {len(tables)}")
    
    for i, tbl in enumerate(tables):
        txt = tbl.get_text(" ", strip=True).upper()
        print(f"\n=== Table {i} ===")
        print(f"Header match 'OPERACAO' and 'CFOP': {'OPERACAO' in txt and 'CFOP' in txt}")
        print(f"Content snippet: {txt[:200]}")
        
        rows = tbl.find_all("tr")
        print(f"Rows: {len(rows)}")
        for j, row in enumerate(rows):
            cols = row.find_all("td")
            vals = [c.get_text(strip=True) for c in cols]
            print(f"  R{j}: {vals}")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
