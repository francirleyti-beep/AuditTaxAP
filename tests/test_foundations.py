import unittest
import logging
from decimal import Decimal
from src.domain.dtos import FiscalItemDTO
from src.domain.exceptions import AuditTaxException, XMLParseException
from src.utils.logging_config import setup_logging
from pathlib import Path
import os

class TestFoundations(unittest.TestCase):
    
    def test_dto_validation_success(self):
        """Testa criação de DTO válido."""
        item = FiscalItemDTO(
            origin="XML",
            item_index=1,
            product_code="123",
            ncm="12345678",
            cest="1234567",
            cfop="5102",
            cst="000",
            amount_total=Decimal("10.00"),
            tax_base=Decimal("10.00"),
            tax_rate=Decimal("18.00"),
            tax_value=Decimal("1.80"),
            mva_percent=Decimal("0"),
            is_suframa_benefit=False
        )
        self.assertEqual(item.origin, "XML")

    def test_dto_validation_invalid_origin(self):
        """Testa erro com origem inválida."""
        with self.assertRaisesRegex(ValueError, "Origin inválida"):
            FiscalItemDTO(
                origin="INVALID",
                item_index=1,
                product_code="123",
                ncm="12345678",
                cest="",
                cfop="5102",
                cst="00",
                amount_total=Decimal("10.00"),
                tax_base=Decimal("10.00"),
                tax_rate=Decimal("18.00"),
                tax_value=Decimal("1.80"),
                mva_percent=Decimal("0"),
                is_suframa_benefit=False
            )

    def test_dto_validation_negative_value(self):
        """Testa erro com valor negativo."""
        with self.assertRaisesRegex(ValueError, "não pode ser negativo"):
            FiscalItemDTO(
                origin="XML",
                item_index=1,
                product_code="123",
                ncm="12345678",
                cest="",
                cfop="5102",
                cst="00",
                amount_total=Decimal("-10.00"), # Negativo
                tax_base=Decimal("10.00"),
                tax_rate=Decimal("18.00"),
                tax_value=Decimal("1.80"),
                mva_percent=Decimal("0"),
                is_suframa_benefit=False
            )

    def test_exceptions_hierarchy(self):
        """Testa hierarquia de exceções."""
        try:
            raise XMLParseException("Erro XML")
        except AuditTaxException:
            pass # Deve capturar
        except Exception:
            self.fail("Deveria ser capturado por AuditTaxException")

    def test_logging_setup(self):
        """Testa configuração de logging."""
        log_file = setup_logging(log_level=logging.DEBUG)
        self.assertTrue(log_file.exists())
        
        logger = logging.getLogger("test_logger")
        logger.info("Teste de log")
        
        # Fechar handlers para liberar arquivo
        handlers = logger.root.handlers[:]
        for handler in handlers:
             handler.close()
             logger.root.removeHandler(handler)

        with open(log_file, "r") as f:
            content = f.read()
            self.assertIn("Teste de log", content)

if __name__ == "__main__":
    unittest.main()
