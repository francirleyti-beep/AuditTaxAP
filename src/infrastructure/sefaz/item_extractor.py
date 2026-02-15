import logging
import re
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Optional, Tuple, Any
from bs4 import BeautifulSoup, Tag, NavigableString
from src.domain.dtos import FiscalItemDTO

class ItemExtractor:
    """
    Extrai dados de itens dos blocos marcados com <h2>ITEM:X</h2>.
    Refatorado para extrair MVA Ajustada, Benefício SUFRAMA monetário,
    e Valor Cobrado (Sefaz) via DOM.
    """
    
    # Regex compilados (otimização)
    CST_PATTERN = re.compile(r'^(\d+)')
    # MVA Ajustada: formato "ALIQUOTA MVA AJUSTADA] =39.51%)" ou "=47.02%)"
    MVA_AJUSTADA_PATTERN = re.compile(r'ALIQUOTA MVA AJUSTADA\]?\s*=?\s*([\d\.]+)%')
    BC_PATTERN = re.compile(r'F\)\s*BASE.*?=\s*([\d\.,]+)')
    ALQ_PATTERN = re.compile(r'ALIQUOTA INTERNA\s*=\s*([\d,]+)%')
    # Benefício SUFRAMA monetário: "BENEFICIO SUFRAMA R$ 540,98" ou "BENEFICIO SUFRAMAR$ 540,98"
    SUFRAMA_VALUE_PATTERN = re.compile(r'BENEFICIO\s+SUFRAMA\s*R\$\s*([\d\.,]+)')
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
        
        # 3. Extrair campos da linha 1 (dados estruturados via h5)
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

        # 6. Extrair valor cobrado via DOM (h2 dentro do TD de CALCULO VALOR)
        sefaz_tax_value = self._extract_sefaz_tax_value(row1)
        
        # 7. Extrair benefício SUFRAMA monetário
        sefaz_benefit_value = self._extract_suframa_value(row1)
        
        # 8. Extrair MVA Ajustada do bloco de cálculo detalhado (row4)
        sefaz_mva_percent = self._extract_mva_ajustada(row4)

        # 9. Montar DTO
        return FiscalItemDTO(
            origin="SEFAZ",
            item_index=item_idx,
            product_code=self._extract_product_code(data_map),
            product_description=data_map.get("PRODUTO", "").strip(),  # [NEW]
            ncm=data_map.get("NCM", "").strip(),
            cest=data_map.get("CEST", "").strip(),
            cfop=cfop,
            cst=self._extract_cst(data_map),
            quantity=Decimal("1.00"),      # [NEW] Default 1.00 (SEFAZ HTML não mostra Qtd clara no Memorial)
            unit_price=sefaz_tax_value,    # [NEW] Placeholder (Valor Total / 1)
            amount_total=sefaz_tax_value,  # Ajustado para usar Valor Cobrado como base de comparação se necessário
            tax_base=self._extract_tax_base(row4),
            tax_rate=self._extract_tax_rate(row4),
            tax_value=sefaz_tax_value,  # Populado com o valor cobrado para compatibilidade
            mva_percent=sefaz_mva_percent,  # Populado com MVA Ajustada para compatibilidade
            is_suframa_benefit=(sefaz_benefit_value > Decimal("0.00")),
            # Campos sefaz_* específicos
            sefaz_tax_value=sefaz_tax_value,
            sefaz_mva_percent=sefaz_mva_percent,
            sefaz_benefit_value=sefaz_benefit_value,
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
    
    def _extract_data_map(self, row) -> Dict[str, str]:
        """
        Extrai pares label→valor de TDs que contêm <h5> labels.
        Corrigido para lidar com múltiplos <h5> no mesmo <td>.
        
        Estratégia: para cada <h5>, pega todo o texto entre ele e o próximo <h5>
        ou fim do <td>, em vez de usar replace que falha com multi-labels.
        """
        data_map = {}
        cols = row.find_all("td")
        for col in cols:
            h5_labels = col.find_all("h5")
            if h5_labels:
                for i, h5 in enumerate(h5_labels):
                    label = h5.get_text(strip=True).upper()
                    # Coletar texto entre este h5 e o próximo h5 (ou fim do td)
                    value_parts = []
                    sibling = h5.next_sibling
                    while sibling:
                        # Parar se encontrar outro h5
                        if isinstance(sibling, Tag) and sibling.name == "h5":
                            break
                        # Pegar texto de NavigableString ou tag que não seja h5
                        if isinstance(sibling, NavigableString):
                            text = str(sibling).strip()
                            if text:
                                value_parts.append(text)
                        elif isinstance(sibling, Tag):
                            text = sibling.get_text(strip=True)
                            if text:
                                value_parts.append(text)
                        sibling = sibling.next_sibling
                    
                    value = " ".join(value_parts).strip()
                    if label not in data_map:
                        data_map[label] = value
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
    
    def _extract_sefaz_tax_value(self, row1) -> Decimal:
        """
        Extrai o Valor Cobrado (Sefaz) buscando o <h2> dentro do TD
        que contém <h5>CALCULO VALOR(Sefaz)</h5>.
        
        HTML esperado:
        <td>
            <h5>CALCULO VALOR(Sefaz)</h5>
            <h3></h3><h2>R$ 455,25</h2>
        </td>
        """
        cols = row1.find_all("td")
        for col in cols:
            h5 = col.find("h5", string=lambda t: t and "CALCULO VALOR" in t.upper())
            if h5:
                # Buscar o <h2> dentro do mesmo TD
                h2_val = col.find("h2")
                if h2_val:
                    return self._parse_money(h2_val.get_text(strip=True))
        return Decimal("0.00")
    
    def _extract_suframa_value(self, row1) -> Decimal:
        """
        Extrai o valor monetário do benefício SUFRAMA.
        Busca regex no texto inteiro da row (pode estar no TD da row1).
        
        HTML esperado:
        <td>
            <h5>BENEFICIO</h5>0<br>
            <h5>BENEFICIO SUFRAMA</h5>R$ 540,98
        </td>
        """
        text = row1.get_text(" ", strip=True)
        match = self.SUFRAMA_VALUE_PATTERN.search(text)
        if match:
            return self._parse_money(match.group(1))
        return Decimal("0.00")
    
    def _extract_mva_ajustada(self, row4) -> Decimal:
        """
        Extrai MVA Ajustada do bloco de cálculo detalhado.
        
        Texto esperado:
        "E)VALOR DA MVA [ D X  ALIQUOTA MVA AJUSTADA] =39.51%) ] =1.567,43"
        
        Nota: O formato usa PONTO como separador decimal (39.51), não vírgula!
        """
        if not row4:
            return Decimal("0.00")
        text = row4.get_text(" ", strip=True)
        match = self.MVA_AJUSTADA_PATTERN.search(text)
        if match:
            try:
                # MVA usa ponto como decimal (39.51, 47.02)
                return Decimal(match.group(1))
            except InvalidOperation:
                self.logger.warning(f"Falha ao converter MVA: {match.group(1)}")
        return Decimal("0.00")

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
    
    def _parse_money(self, text: str) -> Decimal:
        """
        Converte valor monetário brasileiro para Decimal.
        Aceita: "R$ 1.567,43", "1.567,43", "540,98", "455,25"
        Resultado: Decimal("1567.43"), Decimal("540.98"), etc.
        """
        if not text:
            return Decimal("0.00")
        match = self.MONEY_PATTERN.search(text)
        if match:
            val_str = match.group(1).replace(".", "").replace(",", ".")
            try:
                return Decimal(val_str)
            except InvalidOperation:
                self.logger.warning(f"Falha ao converter valor monetário: {text}")
        return Decimal("0.00")
