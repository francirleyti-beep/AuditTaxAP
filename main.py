import sys
import os
from decimal import Decimal

# Adiciona o diretório raiz do projeto ao sys.path para execução correta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.domain.dtos import FiscalItemDTO
from src.core.auditor import AuditEngine

def main():
    print("=== AuditTax AP - Início da Execução ===")
    
    # 1. Simular Dados (Mock)
    # Cenário: XML e SEFAZ idênticos (Sem divergência)
    item_xml = FiscalItemDTO(
        origin="XML", item_index=1, product_code="123", ncm="11223344", cest="0100100", 
        cfop="5405", cst="60", amount_total=Decimal("100.00"), 
        tax_base=Decimal("100.00"), tax_rate=Decimal("18.00"), tax_value=Decimal("18.00"), 
        mva_percent=Decimal("40.00"), is_suframa_benefit=False
    )
    
    item_sefaz = FiscalItemDTO(
        origin="SEFAZ", item_index=1, product_code="123", ncm="11223344", cest="0100100", 
        cfop="5405", cst="60", amount_total=Decimal("100.00"), 
        tax_base=Decimal("100.00"), tax_rate=Decimal("18.00"), tax_value=Decimal("18.00"), 
        mva_percent=Decimal("40.00"), is_suframa_benefit=False
    )
    
    # 2. Executar Auditoria
    engine = AuditEngine()
    result = engine.audit_item(item_xml, item_sefaz)
    
    print(f"Item {result.product_code} - Conforme: {result.is_compliant}")
    if not result.is_compliant:
        for diff in result.differences:
            print(f"  [!] {diff.message}")
            print(f"      XML: {diff.xml_value} | SEFAZ: {diff.sefaz_value}")
    else:
        print("  [OK] Nenhuma divergência encontrada.")

    print("\n=== Teste com Divergência ===")
    # Cenário: SEFAZ cobrando MVA maior (Erro comum)
    item_sefaz_errado = item_sefaz
    item_sefaz_errado.mva_percent = Decimal("50.00") # XML é 40
    
    result_err = engine.audit_item(item_xml, item_sefaz_errado)
    print(f"Item {result_err.product_code} - Conforme: {result_err.is_compliant}")
    if not result_err.is_compliant:
        for diff in result_err.differences:
            print(f"  [!] {diff.message}")
            print(f"      XML: {diff.xml_value} | SEFAZ: {diff.sefaz_value}")

if __name__ == "__main__":
    main()
