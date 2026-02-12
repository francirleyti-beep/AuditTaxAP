import sys
import os
from bs4 import BeautifulSoup
import re

# Output to absolute path file to be sure
log_path = os.path.abspath("cfop_location.txt")
sys.stdout = open(log_path, "w", encoding="utf-8")

path = r"c:\Projetos\AuditTaxAP\tests\samples\52260277595395006269550050000238801206971225\SEFAZ-AP_MATHEUS.html"

with open(path, "r", encoding="windows-1252") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

# Find all strings containing "CFOP"
matches = soup.find_all(string=re.compile("CFOP"))
print(f"Total Matches: {len(matches)}")

for i, m in enumerate(matches):
    print(f"\n--- Match {i} ---")
    print(f"String: {m.strip()}")
    parent = m.find_parent()
    print(f"Parent: {parent.name} (Attrs: {parent.attrs})")
    
    # Climb up to find the container table
    tbl = m.find_parent("table")
    if tbl:
        print(f"Container Table: {tbl.get_text()[:100]}...")
        # Check if rows in this table have item numbers
        rows = tbl.find_all("tr")
        print(f"Rows in this table: {len(rows)}")
        for r_idx, row in enumerate(rows[:5]):
            cols = row.find_all("td")
            vals = [c.get_text(strip=True) for c in cols]
            print(f"  R{r_idx}: {vals}")
    else:
        print("No container table found.")
