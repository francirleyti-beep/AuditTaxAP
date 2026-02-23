import sys
import os

sys.path.append(os.getcwd())

from src.infrastructure.sefaz_scraper import SefazScraper

path = r"c:\Projetos\AuditTaxAP\tests\samples\52260277595395006269550050000238801206971225\SEFAZ-AP_MATHEUS.html"

with open(path, "r", encoding="windows-1252") as f:
    html = f.read()

scraper = SefazScraper()
items = scraper.parse_html(html)

print(f"Total Items: {len(items)}")
for item in items:
    # Print CST with repr to see hidden chars
    print(f"Item {item.item_index}: CST='{item.cst}' | Raw Repr={repr(item.cst)}")
