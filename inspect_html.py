from bs4 import BeautifulSoup
import os

path = r"c:\Projetos\AuditTaxAP\tests\samples\52260277595395006269550050000238801206971225\SEFAZ-AP_MATHEUS.html"

with open(path, "r", encoding="windows-1252") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

print("Labels H5 encontrados:")
for h5 in soup.find_all("h5"):
    print(f" - {h5.get_text(strip=True)}")

print("\nLabels H2 encontrados:")
for h2 in soup.find_all("h2"):
    print(f" - {h2.get_text(strip=True)}")
