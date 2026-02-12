from bs4 import BeautifulSoup

path = r"c:\Projetos\AuditTaxAP\tests\samples\52260277595395006269550050000238801206971225\SEFAZ-AP_MATHEUS.html"

# Tentar ler com utf-8 e latin-1 para garantir
try:
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
except:
    with open(path, "r", encoding="latin-1") as f:
        html = f.read()

soup = BeautifulSoup(html, "html.parser")

target_tables = soup.find_all("table")
resumo_table = None
for tbl in target_tables:
    if "OPERACAO" in tbl.get_text().upper() and "CFOP" in tbl.get_text().upper():
        resumo_table = tbl
        break

if resumo_table:
    # Imprimi apenas as linhas tr para nao poluir mt
    rows = resumo_table.find_all("tr")
    print(f"Total Rows: {len(rows)}")
    for i, row in enumerate(rows):
        print(f"--- Row {i} ---")
        print(row.prettify()[:500]) # truncar para nao estourar buffer
else:
    print("Tabela nao encontrada.")
