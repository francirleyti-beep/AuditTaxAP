import logging
import re
from typing import Dict, Tuple, Optional
from bs4 import BeautifulSoup

class CFOPExtractor:
    """
    Extrai mapa de CFOP da tabela 'INFORMACOES DETALHADAS DA COBRANCA'.
    Mapeia item_index -> CFOP.
    """
    
    # Regex compilado (otimização) - captura 4 dígitos no início
    CFOP_PATTERN = re.compile(r'^(\d{4})')
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract(self, soup: BeautifulSoup) -> Tuple[Dict[int, str], str]:
        """
        Extrai mapa de CFOP.
        Returns: (cfop_map, default_cfop)
        """
        cfop_map = {}
        default_cfop = ""
        
        # Procurar tabela específica
        for table in soup.find_all("table"):
            if self._is_cfop_table(table):
                self.logger.debug("Tabela de CFOP encontrada!")
                cfop_map, default_cfop = self._extract_from_table(table)
                break
        
        self.logger.info(f"CFOP extraídos: {len(cfop_map)} itens, default={default_cfop}")
        return cfop_map, default_cfop
    
    def _is_cfop_table(self, table) -> bool:
        """Verifica se é a tabela de CFOP."""
        text = table.get_text(" ", strip=True).upper()
        keywords = ["INFORMACOES DETALHADAS", "OPERACAO", "CFOP"]
        return all(kw in text for kw in keywords)
    
    def _extract_from_table(self, table) -> Tuple[Dict[int, str], str]:
        """Extrai CFOPs da tabela."""
        cfop_map = {}
        default_cfop = ""
        
        tbody = table.find("tbody") or table
        rows = tbody.find_all("tr")
        
        for row in rows:
            cols = row.find_all("td")
            
            if len(cols) > 2:
                # Coluna 0: Item Index
                item_idx = self._extract_item_index(cols[0])
                
                # Coluna 2: CFOP
                cfop = self._extract_cfop_code(cols[2])
                
                if item_idx and cfop:
                    cfop_map[item_idx] = cfop
                    
                    if not default_cfop:
                        default_cfop = cfop
                    
        return cfop_map, default_cfop
    
    def _extract_item_index(self, cell) -> Optional[int]:
        """Extrai índice do item."""
        text = cell.get_text(strip=True)
        return int(text) if text.isdigit() else None
    
    def _extract_cfop_code(self, cell) -> Optional[str]:
        """Extrai código CFOP de 4 dígitos."""
        text = cell.get_text(strip=True)
        # Regex busca 4 digitos no início (ex: '6110-VENDA...')
        match = self.CFOP_PATTERN.search(text)
        if match:
             return match.group(1)
        # Fallback split
        return text.split("-")[0].strip() if "-" in text else None
