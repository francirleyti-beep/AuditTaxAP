import unittest
from unittest.mock import MagicMock, patch
from src.services.audit_service import AuditService
from src.domain.dtos import FiscalItemDTO, AuditResultDTO, AuditDifference

class TestAuditService(unittest.TestCase):
    
    @patch('src.services.audit_service.XMLReader')
    @patch('src.services.audit_service.SefazScraper')
    @patch('src.services.audit_service.AuditEngine')
    @patch('src.services.audit_service.ReportGenerator')
    def test_process_audit_flow(self, MockReporter, MockAuditor, MockScraper, MockReader):
        # Setup Mocks
        reader_instance = MockReader.return_value
        reader_instance.parse.return_value = ("KEY123", [MagicMock(spec=FiscalItemDTO, item_index=1)])
        
        scraper_instance = MockScraper.return_value
        scraper_instance.fetch_memorial.return_value = [MagicMock(spec=FiscalItemDTO, item_index=1)]
        
        auditor_instance = MockAuditor.return_value
        auditor_instance.audit_item.return_value = AuditResultDTO(
            item_index=1, product_code="TEST", is_compliant=True, differences=[]
        )
        
        reporter_instance = MockReporter.return_value
        reporter_instance.generate_csv.return_value = "report.csv"
        
        # Execute
        service = AuditService()
        result_path = service.process_audit("dummy.xml")
        
        # Verify
        self.assertEqual(result_path, "report.csv")
        reader_instance.parse.assert_called_once_with("dummy.xml")
        scraper_instance.fetch_memorial.assert_called_once_with("KEY123")
        auditor_instance.audit_item.assert_called_once()
        reporter_instance.generate_csv.assert_called_once()

if __name__ == "__main__":
    unittest.main()
