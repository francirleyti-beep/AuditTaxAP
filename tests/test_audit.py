import unittest
import sys
import os
from decimal import Decimal

# Adiciona o diretório raiz do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.domain.dtos import FiscalItemDTO
from src.core.auditor import AuditEngine

class TestAuditEngine(unittest.TestCase):
    def setUp(self):
        self.engine = AuditEngine()
        # Item base "perfeito"
        self.base_item = FiscalItemDTO(
            origin="XML", item_index=1, product_code="TEST", 
            product_description="PRODUTO TESTE",
            ncm="12345678", cest="0100100", cfop="5102", cst="000",
            icms_orig="0",
            quantity=Decimal("1.00"), unit_price=Decimal("100.00"),
            amount_total=Decimal("100.00"), tax_base=Decimal("100.00"),
            tax_rate=Decimal("18.00"), tax_value=Decimal("0.00"),
            mva_percent=Decimal("0.00"), is_suframa_benefit=False
        )

    def test_audit_success(self):
        # Para sucesso, XML e SEFAZ devem concordar que há ST de 18.00
        item_xml = FiscalItemDTO(**self.base_item.__dict__)
        item_xml.icms_st_value = Decimal("18.00")
        item_xml.icms_st_base = Decimal("100.00")
        
        item_sefaz = FiscalItemDTO(**self.base_item.__dict__)
        item_sefaz.origin = "SEFAZ"
        item_sefaz.sefaz_tax_value = Decimal("18.00")
        item_sefaz.tax_base = Decimal("100.00")
        item_sefaz.tax_rate = Decimal("18.00")
        
        result = self.engine.audit_item(item_xml, item_sefaz)
        self.assertTrue(result.is_compliant, f"Item should be compliant. Diffs: {result.differences}")
        self.assertEqual(len(result.differences), 0)

    def test_audit_failure_mva(self):
        item_xml = FiscalItemDTO(**self.base_item.__dict__)
        item_xml.icms_st_value = Decimal("18.00")
        
        item_sefaz = FiscalItemDTO(**self.base_item.__dict__) 
        item_sefaz.origin = "SEFAZ"
        item_sefaz.sefaz_tax_value = Decimal("18.00")
        item_sefaz.sefaz_mva_percent = Decimal("10.00")
        item_sefaz.mva_percent = Decimal("10.00") 
        item_sefaz.tax_rate = Decimal("18.00")
        
        result = self.engine.audit_item(item_xml, item_sefaz)
        self.assertFalse(result.is_compliant)
        # 1. Alíquota MVA divergente (MVARule)
        # 2. Valor cobrado diverge do cálculo matemático (SefazCalculationRule)
        #    Cálculo: 100 * (1 + 10%) * 18% = 19.80. Cobrado 18.00.
        self.assertGreaterEqual(len(result.differences), 2)

if __name__ == '__main__':
    unittest.main()
