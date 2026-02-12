import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.infrastructure.sefaz_scraper import SefazScraper

# Define output file
log_path = os.path.abspath("cfop_validation.log")

try:
    with open(log_path, "w", encoding="utf-8") as log:
        log.write("Iniciando Validacao CFOP...\n")
        
        path = r"c:\Projetos\AuditTaxAP\tests\samples\52260277595395006269550050000238801206971225\SEFAZ-AP_MATHEUS.html"
        log.write(f"Lendo HTML: {path}\n")

        with open(path, "r", encoding="windows-1252") as f: # Try windows-1252
            html = f.read()

        scraper = SefazScraper()
        items = scraper.parse_html(html)

        log.write(f"Total Items Extraidos: {len(items)}\n")
        for item in items:
            log.write(f"Item {item.item_index}: CFOP='{item.cfop}' | CST='{item.cst}'\n")
            
        log.write("Fim da Validacao.\n")

    print(f"Validacao concluida. Log escrito em: {log_path}")

except Exception as e:
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\nERRO: {str(e)}\n")
    print(f"Erro na validacao: {e}")
