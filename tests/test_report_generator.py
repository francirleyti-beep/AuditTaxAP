import unittest
import os

from src.presentation.report_generator import ReportGenerator
from src.domain.dtos import AuditResultDTO, AuditDifference

class TestReportGenerator(unittest.TestCase):
    def test_generate_csv(self):
        generator = ReportGenerator()
        
        # Dados mock
        results = [
            AuditResultDTO(
                item_index=1, 
                product_code="TEST001", 
                is_compliant=True, 
                differences=[]
            ),
            AuditResultDTO(
                item_index=2, 
                product_code="TEST002", 
                is_compliant=False, 
                differences=[
                    AuditDifference(field="NCM", xml_value="123", sefaz_value="456", message="Div NCM")
                ]
            )
        ]
        
        # Executa
        output_file = "test_report.csv"
        generated_path = generator.generate_csv(results, output_file)
        
        # Verifica
        self.assertIsNotNone(generated_path)
        self.assertTrue(os.path.exists(output_file))
        
        # Opcional: Ler conteúdo
        with open(output_file, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            self.assertIn("TEST001", content)
            self.assertIn("Div NCM", content)
            
        # Limpeza
        if os.path.exists(output_file):
            os.remove(output_file)

if __name__ == "__main__":
    unittest.main()
