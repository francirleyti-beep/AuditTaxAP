"""
Script de verificação: testa a extração do InvoiceDTO e a validação de consistência.
"""
import sys
import os
# Adicionar raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from decimal import Decimal
from src.infrastructure.xml_reader import XMLReader
from src.core.invoice_validator import InvoiceValidator

def main():
    # Caminho do XML de amostra
    xml_path = os.path.join(
        "tests", "samples", 
        "52260277595395006269550050000238801206971225.xml"
    )
    
    if not os.path.exists(xml_path):
        print(f"ERRO: XML não encontrado em {xml_path}")
        return False

    print(f"Lendo XML: {xml_path}")
    
    reader = XMLReader()
    try:
        invoice = reader.parse(xml_path)
    except Exception as e:
        print(f"❌ Erro ao processar XML: {e}")
        return False

    print("=" * 80)
    print("DADOS EXTRAÍDOS DO XML (InvoiceDTO)")
    print("=" * 80)
    print(f"Chave NFe: {invoice.access_key}")
    print(f"Número: {invoice.number} | Série: {invoice.series}")
    print(f"Emissão: {invoice.issue_date}")
    print(f"Emitente: {invoice.emitter_name} (CNPJ: {invoice.emitter_cnpj})")
    print(f"Destinatário: {invoice.recipient_name} (Doc: {invoice.recipient_doc})")
    print(f"Protocolo: {invoice.protocol_number} em {invoice.protocol_date}")
    print("-" * 80)
    print(f"Total Produtos (vProd): R$ {invoice.total_products}")
    print(f"Total Nota (vNF): R$ {invoice.total_invoice}")
    print(f"Total ICMS (vICMS): R$ {invoice.total_icms}")
    print("-" * 80)
    print(f"Total de Itens: {len(invoice.items)}")
    
    # Validar alguns itens
    if len(invoice.items) > 0:
        item1 = invoice.items[0]
        print(f"Item 1: {item1.product_code} - {item1.product_description}")
        print(f"        Qtd: {item1.quantity} | Unit: R$ {item1.unit_price} | Total: R$ {item1.amount_total}")

    print("=" * 80)
    print("VALIDAÇÃO DE CONSISTÊNCIA INTERNA")
    print("=" * 80)
    
    validator = InvoiceValidator()
    errors = validator.validate(invoice)
    
    if not errors:
        print("✅ Nenhuma inconsistência encontrada no XML.")
    else:
        print(f"⚠️ Encontrados {len(errors)} problemas de consistência:")
        for err in errors:
            print(f"  [{err.field}] {err.message}")
            print(f"     XML: {err.xml_value} | Ref: {err.sefaz_value}")

    print("=" * 80)
    
    # Verificações manuais de sanidade
    all_ok = True
    
    # 1. Verificar se valores não estão zerados (assumindo que o XML tem valores)
    if invoice.total_products == 0 and len(invoice.items) > 0:
        print("❌ ALERTA: Total de Produtos zerado, mas há itens.")
        all_ok = False
        
    if invoice.emitter_name == "":
        print("❌ ALERTA: Nome do Emitente não extraído.")
        all_ok = False

    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
