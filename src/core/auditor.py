from decimal import Decimal
from typing import Optional
from src.domain.dtos import FiscalItemDTO, AuditResultDTO, AuditDifference
from src.core.calculator import TaxCalculator

class AuditEngine:
    """
    Motor de auditoria que compara o item do XML contra o item da SEFAZ
    e valida regras de negócio.
    """
    
    def __init__(self):
        self.calculator = TaxCalculator()
        self.tolerance = Decimal("0.05") # R$ 0,05 de tolerância conforme RF05

    def audit_item(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> AuditResultDTO:
        differences = []

        # 1. Auditoria Cadastral (RF04)
        self._check_equality(differences, "NCM", xml_item.ncm, sefaz_item.ncm)
        self._check_equality(differences, "CEST", xml_item.cest, sefaz_item.cest)
        self._check_equality(differences, "CFOP", xml_item.cfop, sefaz_item.cfop)
        self._check_equality(differences, "CST", xml_item.cst, sefaz_item.cst)

        # 2. Auditoria de Valores (RF05)
        # Verifica se o valor cobrado pela sefaz bate com o calculado (ou XML vs SEFAZ direto)
        # Aqui comparamos XML vs SEFAZ nos valores monetários principais
        self._check_monetary(differences, "Base de Cálculo", xml_item.tax_base, sefaz_item.tax_base)
        self._check_monetary(differences, "Valor ICMS", xml_item.tax_value, sefaz_item.tax_value)
        self._check_monetary(differences, "MVA %", xml_item.mva_percent, sefaz_item.mva_percent)

        is_compliant = len(differences) == 0
        
        return AuditResultDTO(
            item_index=xml_item.item_index,
            product_code=xml_item.product_code,
            is_compliant=is_compliant,
            differences=differences
        )

    def _check_equality(self, diffs: list, field_name: str, val1: str, val2: str):
        if val1 != val2:
            diffs.append(AuditDifference(
                field=field_name,
                xml_value=str(val1),
                sefaz_value=str(val2),
                message=f"Divergência de cadastro em {field_name}"
            ))

    def _check_monetary(self, diffs: list, field_name: str, val1: Decimal, val2: Decimal):
        delta = abs(val1 - val2)
        if delta > self.tolerance:
            diffs.append(AuditDifference(
                field=field_name,
                xml_value=str(val1),
                sefaz_value=str(val2),
                message=f"Divergência de valor em {field_name} (Dif: {delta})"
            ))
