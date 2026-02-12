import unittest
import os
import sys
# Adiciona o diretório raiz do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal
from src.infrastructure.xml_reader import XMLReader

class TestXMLReader(unittest.TestCase):
    def setUp(self):
        self.reader = XMLReader()
        # Caminho relativo ao root do projeto, assumindo execução da raiz
        self.sample_xml = os.path.join("tests", "samples", "nfe_sample.xml")

    def test_parse_sample(self):
        items = self.reader.parse(self.sample_xml)
        
        self.assertEqual(len(items), 2, "Deve encontrar 2 itens no XML de amostra")
        
        # Item 1: Normal
        item1 = items[0]
        self.assertEqual(item1.product_code, "PROD-001")
        self.assertEqual(item1.ncm, "22021000")
        self.assertEqual(item1.cst, "00")
        self.assertEqual(item1.tax_value, Decimal("18.00"))
        self.assertFalse(item1.is_suframa_benefit)

        # Item 2: Suframa
        item2 = items[1]
        self.assertEqual(item2.product_code, "PROD-002-SUFRAMA")
        self.assertEqual(item2.ncm, "84713012")
        self.assertEqual(item2.cst, "40") # Isento/No tributado
        self.assertTrue(item2.is_suframa_benefit, "Deve identificar benefcio Suframa (motDesICMS=7)")
        self.assertEqual(item2.tax_value, Decimal("0.00"), "ICMS deve ser zero para CST 40")

if __name__ == '__main__':
    unittest.main()
