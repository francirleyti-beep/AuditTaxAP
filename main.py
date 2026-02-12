import sys
import os
from decimal import Decimal

# Adiciona o diretório raiz do projeto ao sys.path para execução correta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.domain.dtos import FiscalItemDTO
from src.core.auditor import AuditEngine
from src.infrastructure.xml_reader import XMLReader
from src.infrastructure.sefaz_scraper import SefazScraper
from src.presentation.report_generator import ReportGenerator

def main():
    print("=== AuditTax AP - Auditoria Fiscal ===")
    
    # 1. Obter arquivo XML
    xml_path = input("Digite o caminho do arquivo XML (ex: tests/samples/nfe_sample.xml): ").strip()
    if not xml_path:
        xml_path = os.path.join("tests", "samples", "nfe_sample.xml")
        print(f"Usando arquivo padrão: {xml_path}")

    if not os.path.exists(xml_path):
        print("Arquivo não encontrado!")
        return

    # 2. Ler XML
    print("\n[1/4] Lendo XML...")
    reader = XMLReader()
    try:
        nfe_key, xml_items = reader.parse(xml_path)
        print(f"Chave NFe detectada: {nfe_key}")
        print(f"Encontrados {len(xml_items)} itens no XML.")
    except Exception as e:
        print(f"Erro ao ler XML: {e}")
        return

    # 3. Buscar Dados na SEFAZ
    print("\n[2/4] Iniciando Scraper SEFAZ...")
    
    if not nfe_key:
        nfe_key = input("Chave não encontrada no XML. Digite a chave de acesso (44 dígitos): ").strip()

    scraper = SefazScraper()
    sefaz_items = scraper.fetch_memorial(nfe_key)
    
    if not sefaz_items:
        print("Nenhum item retornado da SEFAZ ou erro no scraping.")
        return

    print(f"Retornados {len(sefaz_items)} itens da SEFAZ.")

    # 4. Auditar
    print("\n[3/4] Auditando Itens...")
    engine = AuditEngine()
    
    sefaz_map = {item.item_index: item for item in sefaz_items}
    audit_results = []

    for xml_item in xml_items:
        idx = xml_item.item_index
        sefaz_item = sefaz_map.get(idx)
        
        print(f"\n--- Item {idx}: {xml_item.product_code} ---")
        
        if not sefaz_item:
            print(f"  [ERRO] Item {idx} não encontrado na SEFAZ.")
            continue
            
        result = engine.audit_item(xml_item, sefaz_item)
        audit_results.append(result)
        
        if result.is_compliant:
            print("  [OK] Conforme.")
        else:
            print("  [DIVERGÊNCIA ENCONTRADA]")
            for diff in result.differences:
                print(f"    - {diff.message}")
                print(f"      XML: {diff.xml_value} | SEFAZ: {diff.sefaz_value}")

    # 5. Gerar Relatório
    print("\n[4/4] Gerando Relatório...")
    reporter = ReportGenerator()
    reporter.generate_excel(audit_results)

    print("\n=== Auditoria Finalizada ===")

if __name__ == "__main__":
    main()
