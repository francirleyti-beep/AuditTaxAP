import unittest
from unittest.mock import Mock, MagicMock
from bs4 import BeautifulSoup
from src.infrastructure.sefaz.cfop_extractor import CFOPExtractor
from src.infrastructure.sefaz.item_extractor import ItemExtractor
from src.domain.dtos import FiscalItemDTO

class TestModularScraper(unittest.TestCase):
    
    def test_cfop_extractor(self):
        html = """
        <table>
            <tbody>
                <tr><td>INFORMACOES DETALHADAS DA COBRANCA</td></tr>
                <tr><td>OPERACAO - CFOP</td></tr>
                <tr>
                    <td>1</td>
                    <td>ICMS</td>
                    <td>6110 - VENDA DE MERCADORIA</td>
                </tr>
            </tbody>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        extractor = CFOPExtractor()
        cfop_map, default = extractor.extract(soup)
        
        self.assertEqual(cfop_map[1], "6110")
        self.assertEqual(default, "6110")

    def test_item_extractor(self):
        html = """
        <table>
            <tr><td><h2>ITEM: 1</h2></td></tr>
            <tr>
                <td><h5>PRODUTO</h5>COD123 DESC</td>
                <td><h5>NCM</h5>12345678</td>
                <td><h5>CST</h5>040 ST DEST</td>
                <td><h5>CALCULO VALOR(SEFAZ)</h5>R$ 10,00</td>
            </tr>
            <tr></tr> <!-- row2 -->
            <tr><td>MVA ORIGINAL 30,00%</td></tr> <!-- row3 -->
            <tr><td>ALIQUOTA INTERNA = 18,00% F) BASE CALCULO = 100,00</td></tr> <!-- row4 -->
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        extractor = ItemExtractor()
        cfop_map = {1: "6110"}
        
        items = extractor.extract(soup, cfop_map)
        
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item.item_index, 1)
        self.assertEqual(item.cfop, "6110")
        self.assertEqual(item.cst, "040")
        self.assertEqual(item.product_code, "COD123")
        
    def test_item_extractor_default_cfop(self):
         # Item 2 sem entrada no mapa, deve usar default
        html = """
        <table>
            <tr><td><h2>ITEM: 2</h2></td></tr>
            <tr>
                <td><h5>PRODUTO</h5>COD123</td>
                <td><h5>CST</h5>040</td>
            </tr>
            <tr></tr><tr></tr><tr></tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        extractor = ItemExtractor()
        cfop_map = {1: "6110"}
        default_cfop = "6110"
        
        items = extractor.extract(soup, cfop_map, default_cfop)
        item = items[0]
        self.assertEqual(item.cfop, "6110")

if __name__ == "__main__":
    unittest.main()
