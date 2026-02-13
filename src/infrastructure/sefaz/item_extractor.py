import logging
import re
from decimal import Decimal
from typing import List, Dict, Optional, Tuple, Any
from bs4 import BeautifulSoup
from src.domain.dtos import FiscalItemDTO

class ItemExtractor:
    """
    Extrai dados de itens dos blocos marcados com <h2>ITEM:X</h2>.
    """
    
    # Regex compilados (otimização)
    CST_PATTERN = re.compile(r'^(\d+)')
    MVA_PATTERN = re.compile(r'MVA ORIGINAL\s*([\d,]+)%')
    BC_PATTERN = re.compile(r'F\)\s*BASE.*?=\s*([\d\.,]+)')
    ALQ_PATTERN = re.compile(r'ALIQUOTA INTERNA\s*=\s*([\d,]+)%')
    # Regex monetário flexível: aceita 'R$ 1.234,56' e '1.234,56'
    MONEY_PATTERN = re.compile(r'(?:R\$\s*)?([\d\.]+,\d{2})')
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract(self, soup: BeautifulSoup, cfop_map: Dict[int, str], default_cfop: str = "") -> List[FiscalItemDTO]:
        """
        Extrai todos os itens fiscais.
        """
        items = []
        
        # Encontrar blocos H2
        h2_headers = soup.find_all("h2", string=lambda t: t and t.strip().startswith("ITEM:"))
        self.logger.info(f"Encontrados {len(h2_headers)} blocos de itens")
        
        for h2 in h2_headers:
            try:
                item = self._extract_single_item(h2, cfop_map, default_cfop)
                if item:
                    items.append(item)
            except Exception as e:
                self.logger.error(f"Erro ao extrair item do bloco H2: {e}", exc_info=True)
                continue
        
        return items
    
    def _extract_single_item(self, h2, cfop_map: Dict[int, str], default_cfop: str) -> Optional[FiscalItemDTO]:
        """Extrai dados de um único item."""
        # 1. Extrair índice
        item_idx = self._extract_item_index(h2)
        if not item_idx:
            return None
        
        # 2. Navegar estrutura HTML
        row1 = self._find_parent_row(h2)
        if not row1:
            return None
        
        # 3. Extrair campos da linha 1
        data_map = self._extract_data_map(row1)
        
        # 4. Obter linhas seguintes
        row2, row3, row4 = self._get_sibling_rows(row1)

        # Fallback: Se não achou dados na linha 1, tenta linha 2 (Layout B)
        if not data_map and row2:
             data_map = self._extract_data_map(row2)
        
        # 5. Definir CFOP (Prioridade: Mapa > Default > DataMap)
        cfop = cfop_map.get(item_idx, default_cfop)
        if not cfop:
             # Fallback da ficha
             cfop_full = data_map.get("OPERACAO", "") or data_map.get("NATUREZA", "")
             match = re.search(r'^(\d{4})', cfop_full.strip())
             cfop = match.group(1) if match else ""

        # 6. Montar DTO
        return FiscalItemDTO(
            origin="SEFAZ",
            item_index=item_idx,
            product_code=self._extract_product_code(data_map),
            ncm=data_map.get("NCM", "").strip(),
            cest=data_map.get("CEST", "").strip(),
            cfop=cfop,
            cst=self._extract_cst(data_map),
            amount_total=Decimal("0.00"),  # Não extraído explicitamente como total do item na ficha
            tax_base=self._extract_tax_base(row4),
            tax_rate=self._extract_tax_rate(row4),
            tax_value=self._extract_tax_value(data_map),
            mva_percent=self._extract_mva(row3),
            is_suframa_benefit=self._detect_suframa(row4)
        )
    
    # --- Helpers ---
    
    def _extract_item_index(self, h2) -> Optional[int]:
        """Extrai índice do item do H2."""
        h2_text = h2.get_text(strip=True).replace("ITEM:", "")
        # Remove texto extra (ex: 'ITEM:1 - ...')
        if ":" in h2_text: h2_text = h2_text.split(":")[0] 
        h2_text = h2_text.strip().split(" ")[0]
        return int(h2_text) if h2_text.isdigit() else None
    
    def _find_parent_row(self, h2) -> Optional[Any]:
        td_item = h2.find_parent("td")
        return td_item.find_parent("tr") if td_item else None
    
    def _get_sibling_rows(self, row1) -> Tuple[Optional[Any], Optional[Any], Optional[Any]]:
        row2 = row1.find_next_sibling("tr")
        row3 = row2.find_next_sibling("tr") if row2 else None
        row4 = row3.find_next_sibling("tr") if row3 else None
        return row2, row3, row4
    
    def _extract_data_map(self, row1) -> Dict[str, str]:
        data_map = {}
        cols = row1.find_all("td")
        for col in cols:
            h5_labels = col.find_all("h5")
            if h5_labels:
                full_text = col.get_text(" ", strip=True)
                for h5 in h5_labels:
                    label = h5.get_text(strip=True).upper()
                    # Remove label do texto para pegar valor
                    # Estrategia simples: replace
                    val_text = full_text.replace(h5.get_text(strip=True), "").strip()
                    # Se houver multiplos labels na mesma TD, isso pode ser impreciso, 
                    # mas para o layout atual funciona. Refinamento possível se necessário.
                    if label not in data_map:
                         data_map[label] = val_text
            else:
                 # Caso especial: Valor Total as vezes vem solto com R$
                 if "R$" in col.get_text():
                     data_map["VALOR_TOTAL"] = col.get_text(strip=True)
        return data_map

    def _extract_product_code(self, data_map) -> str:
        prod = data_map.get("PRODUTO", "")
        return prod.split(" ")[0] if prod else ""
    
    def _extract_cst(self, data_map) -> str:
        cst_raw = data_map.get("CST", "").strip()
        match = self.CST_PATTERN.search(cst_raw)
        return match.group(1) if match else ""
    
    def _extract_tax_value(self, data_map) -> Decimal:
        val_raw = (data_map.get("CALCULO VALOR(SEFAZ)", "") or 
                   data_map.get("CALCULO VALOR (SEFAZ)", "") or
                   data_map.get("VALOR_TOTAL", ""))
        return self._parse_money(val_raw)
    
    def _extract_mva(self, row3) -> Decimal:
        if not row3: return Decimal("0.00")
        text = row3.get_text(strip=True)
        match = self.MVA_PATTERN.search(text)
        return Decimal(match.group(1).replace(",", ".")) if match else Decimal("0.00")

    def _extract_tax_base(self, row4) -> Decimal:
        if not row4: return Decimal("0.00")
        text = row4.get_text(strip=True)
        match = self.BC_PATTERN.search(text)
        return self._parse_money(match.group(1)) if match else Decimal("0.00")

    def _extract_tax_rate(self, row4) -> Decimal:
        if not row4: return Decimal("0.00")
        text = row4.get_text(strip=True)
        match = self.ALQ_PATTERN.search(text)
        return Decimal(match.group(1).replace(",", ".")) if match else Decimal("0.00")
    
    def _detect_suframa(self, row4) -> bool:
        if not row4: return False
        return "DESONERACAO DA SUFRAMA" in row4.get_text(" ", strip=True).upper()
        
    def _parse_money(self, text: str) -> Decimal:
        if not text: return Decimal("0.00")
        match = self.MONEY_PATTERN.search(text)
        if match:
            val_str = match.group(1).replace(".", "").replace(",", ".")
            return Decimal(val_str)
        return Decimal("0.00")
