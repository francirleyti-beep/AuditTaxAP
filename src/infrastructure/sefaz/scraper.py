import logging
from typing import List
from src.domain.dtos import FiscalItemDTO
from src.domain.exceptions import SefazScraperException
from src.infrastructure.sefaz.driver_manager import SeleniumDriverManager
from src.infrastructure.sefaz.driver_manager import SeleniumDriverManager
from src.infrastructure.sefaz.html_parser import SefazHTMLParser
from src.utils.config import Config

class SefazScraper:
    """
    Fachada para scraping da SEFAZ.
    Substitui a antiga implementação monolítica.
    """
    
    def __init__(self, headless: bool = None):
        self.headless = headless if headless is not None else Config.is_headless()
        self.parser = SefazHTMLParser()
        self.logger = logging.getLogger(__name__)
    
    def fetch_memorial(self, nfe_key: str, xml_path: str = None) -> List[FiscalItemDTO]:
        """
        Busca memorial da SEFAZ para uma NFe.
        """
        self.logger.info(f"Buscando memorial SEFAZ: {nfe_key}")
        
        try:
            # Context manager garante fechamento do driver
            with SeleniumDriverManager(self.headless) as driver_mgr:
                # Tenta resolver captcha automaticamente
                driver_mgr.resolve_captcha_and_submit(nfe_key)
                
                # Extrair HTML
                html = driver_mgr.get_page_source()
                
                # Parsear
                items = self.parser.parse(html)
                
                return items
                
        except Exception as e:
            self.logger.error(f"Erro no scraping: {e}", exc_info=True)
            # Se for erro conhecido, re-raise, senão envelopa
            if isinstance(e, SefazScraperException):
                raise e
            raise SefazScraperException(f"Falha ao buscar memorial: {e}")

    def parse_html(self, html: str) -> List[FiscalItemDTO]:
        """
        Método de compatibilidade para parsing direto de HTML string.
        Utilizado principalmente em testes.
        """
        return self.parser.parse(html)
