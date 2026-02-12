import unittest
import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal
from src.domain.dtos import FiscalItemDTO
from src.core.auditor import AuditEngine

class TestAuditEngine(unittest.TestCase):
    def setUp(self):
        self.engine = AuditEngine()
        self.base_item = FiscalItemDTO(
            origin="XML", item_index=1, product_code="TEST", 
            ncm="12345678", cest="0100100", cfop="5102", cst="00",
            amount_total=Decimal("100.00"), tax_base=Decimal("100.00"),
            tax_rate=Decimal("18.00"), tax_value=Decimal("18.00"),
            mva_percent=Decimal("0.00"), is_suframa_benefit=False
        )

    def test_audit_success(self):
        item_xml = self.base_item
        item_sefaz = self.base_item # Clone identical
        
        result = self.engine.audit_item(item_xml, item_sefaz)
        self.assertTrue(result.is_compliant, "Item should be compliant when identical")
        self.assertEqual(len(result.differences), 0)

    def test_audit_failure_mva(self):
        item_xml = self.base_item
        # Clone and modify
        item_sefaz = FiscalItemDTO(**self.base_item.__dict__) 
        item_sefaz.origin = "SEFAZ"
        item_sefaz.mva_percent = Decimal("10.00") # Divergence
        
        result = self.engine.audit_item(item_xml, item_sefaz)
        self.assertFalse(result.is_compliant)
        self.assertEqual(len(result.differences), 1)
        self.assertIn("MVA %", result.differences[0].message)

if __name__ == '__main__':
    unittest.main()
