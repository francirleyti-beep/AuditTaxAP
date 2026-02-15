from decimal import Decimal
from typing import List, Optional
from src.domain.dtos import InvoiceDTO, AuditDifference, AuditResultDTO

class InvoiceValidator:
    """
    Validador de consistência interna da Nota Fiscal (XML).
    Verifica se os totais batem com a soma dos itens e outras regras lógicas.
    """

    def validate(self, invoice: InvoiceDTO) -> List[AuditDifference]:
        differences = []

        # 1. Validar Total dos Produtos (vProd)
        sum_products = sum(item.amount_total for item in invoice.items)
        if abs(invoice.total_products - sum_products) > Decimal("0.05"):
            differences.append(AuditDifference(
                field="CONSISTENCIA_TOTAL_PRODUTOS",
                xml_value=f"{invoice.total_products:.2f}",
                sefaz_value=f"{sum_products:.2f} (Soma Itens)",
                message=f"Total vProd ({invoice.total_products}) diverge da soma dos itens ({sum_products})"
            ))

        # 2. Validar Total ICMS (vICMS)
        sum_icms = sum(item.tax_value for item in invoice.items)
        # Tolerância maior para ICMS devido a arredondamentos item a item
        if abs(invoice.total_icms - sum_icms) > Decimal("0.10"): 
            differences.append(AuditDifference(
                field="CONSISTENCIA_TOTAL_ICMS",
                xml_value=f"{invoice.total_icms:.2f}",
                sefaz_value=f"{sum_icms:.2f} (Soma Itens)",
                message=f"Total vICMS ({invoice.total_icms}) diverge da soma dos itens ({sum_icms})"
            ))

        # 3. Validar CST vs ICMS (Lógica de Negócio)
        for item in invoice.items:
            # CST 00 (Tributada Integralmente) deve ter base e valor de ICMS
            if item.cst == "00":
                if item.tax_base <= 0 or item.tax_value <= 0:
                    differences.append(AuditDifference(
                        field=f"CONSISTENCIA_CST00_ITEM_{item.item_index}",
                        xml_value=f"CST {item.cst} | vBC {item.tax_base} | vICMS {item.tax_value}",
                        sefaz_value="Requer valor > 0",
                        message="CST 00 exige base de cálculo e valor de ICMS positivos"
                    ))
            
            # CST 40/41/50 (Isento/Não Tributado/Suspensão) deve ter ICMS zerado
            if item.cst in ["40", "41", "50"]:
                if item.tax_value > 0:
                     differences.append(AuditDifference(
                        field=f"CONSISTENCIA_CST{item.cst}_ITEM_{item.item_index}",
                        xml_value=f"vICMS {item.tax_value}",
                        sefaz_value="0.00",
                        message=f"CST {item.cst} não deve ter valor de ICMS"
                    ))

        return differences
