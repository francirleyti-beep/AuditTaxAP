import logging
from typing import List
from bs4 import BeautifulSoup
from src.domain.dtos import FiscalItemDTO
from src.domain.exceptions import SefazScraperException
from src.infrastructure.sefaz.cfop_extractor import CFOPExtractor
from src.infrastructure.sefaz.item_extractor import ItemExtractor

class SefazHTMLParser:
    """
    Orquestra a extração de dados do HTML.
    Coordena CFOPExtractor e ItemExtractor.
    """
    
    def __init__(self):
        self.cfop_extractor = CFOPExtractor()
        self.item_extractor = ItemExtractor()
        self.logger = logging.getLogger(__name__)
    
    def parse(self, html: str) -> List[FiscalItemDTO]:
        """
        Parseia HTML e retorna itens fiscais.
        """
        self.logger.info("Iniciando parse do HTML...")
        
        # Parse com BeautifulSoup (preferencialmente lxml se disponível)
        try:
             soup = BeautifulSoup(html, "lxml")
        except:
             soup = BeautifulSoup(html, "html.parser")
        
        # 1. Extrair mapa de CFOP
        cfop_map, default_cfop = self.cfop_extractor.extract(soup)
        
        # 2. Extrair itens
        items = self.item_extractor.extract(soup, cfop_map, default_cfop)
        
        # 3. Validar
        if not items:
            self._save_debug_html(html)
            raise SefazScraperException("Nenhum item extraído do HTML (Scraper v2 falhou)")
        
        self.logger.info(f"✓ Parse concluído: {len(items)} itens extraídos")
        return items
    
    def _save_debug_html(self, html: str):
        """Salva HTML para debug quando falha."""
        debug_file = "debug_sefaz_error_v2.html"
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(html)
        self.logger.error(f"HTML salvo para debug em: {debug_file}")
