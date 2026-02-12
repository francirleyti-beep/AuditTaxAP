import unittest
from decimal import Decimal
from src.core.auditor import AuditEngine
from src.domain.dtos import FiscalItemDTO

class TestStrategicAuditor(unittest.TestCase):
    
    def setUp(self):
        self.engine = AuditEngine()
        
        # DTO Base
        self.base_item = FiscalItemDTO(
            origin="XML",
            item_index=1,
            product_code="PROD001",
            ncm="12345678",
            cest="1234567",
            cfop="5102",
            cst="000",
            amount_total=Decimal("100.00"),
            tax_base=Decimal("100.00"),
            tax_rate=Decimal("18.00"),
            tax_value=Decimal("18.00"), # 18% de 100
            mva_percent=Decimal("0.00"),
            is_suframa_benefit=False
        )

    def test_compliant_item(self):
        """Testa item 100% igual."""
        xml = self.base_item
        sefaz = self.base_item # Clone
        
        result = self.engine.audit_item(xml, sefaz)
        self.assertTrue(result.is_compliant)
        self.assertEqual(len(result.differences), 0)

    def test_ncm_divergence(self):
        """Testa regra de NCM."""
        xml = self.base_item
        # Clone alterando NCM
        sefaz = FiscalItemDTO(**self.base_item.__dict__)
        sefaz.ncm = "87654321"
        
        result = self.engine.audit_item(xml, sefaz)
        self.assertFalse(result.is_compliant)
        self.assertEqual(len(result.differences), 1)
        self.assertEqual(result.differences[0].field, "NCM")

    def test_cst_normalization(self):
        """Testa normalização de CST (40 vs 040)."""
        xml = FiscalItemDTO(**self.base_item.__dict__)
        xml.cst = "40" # XML as vezes vem sem zero esq
        
        sefaz = FiscalItemDTO(**self.base_item.__dict__)
        sefaz.cst = "040"
        
        result = self.engine.audit_item(xml, sefaz)
        self.assertTrue(result.is_compliant, "CST '40' vs '040' deve ser compatível")

    def test_monetary_tolerance(self):
        """Testa tolerância monetária (0.05)."""
        xml = FiscalItemDTO(**self.base_item.__dict__)
        xml.tax_value = Decimal("18.00")
        
        sefaz = FiscalItemDTO(**self.base_item.__dict__)
        sefaz.tax_value = Decimal("18.04") # Diferença 0.04 < 0.05
        
        result = self.engine.audit_item(xml, sefaz)
        self.assertTrue(result.is_compliant, "Diferença de 0.04 deve ser aceita")
        
        sefaz.tax_value = Decimal("18.06") # Diferença 0.06 > 0.05
        result = self.engine.audit_item(xml, sefaz)
        self.assertFalse(result.is_compliant)
        self.assertEqual(result.differences[0].field, "TAX_VALUE")

if __name__ == "__main__":
    unittest.main()
