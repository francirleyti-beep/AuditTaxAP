from dataclasses import dataclass
from decimal import Decimal

@dataclass
class FiscalItemDTO:
    """
    Data Transfer Object que representa um item fiscal normalizado.
    Pode ser originado de um XML de NFe ou de uma linha do Memorial da SEFAZ.
    """
    origin: str  # 'XML' ou 'SEFAZ'
    item_index: int
    product_code: str
    ncm: str
    cest: str
    cfop: str
    cst: str
    amount_total: Decimal
    tax_base: Decimal
    tax_rate: Decimal
    tax_value: Decimal
    mva_percent: Decimal
    is_suframa_benefit: bool

    def __post_init__(self):
        """Validações básicas após inicialização."""
        if self.origin not in ['XML', 'SEFAZ']:
            raise ValueError(f"Origin inválida: {self.origin}")
        
        if self.item_index <= 0:
            raise ValueError(f"item_index deve ser positivo: {self.item_index}")
            
        # Validar valores monetários não negativos
        monetary_fields = ['amount_total', 'tax_base', 'tax_rate', 'tax_value', 'mva_percent']
        for field in monetary_fields:
            val = getattr(self, field)
            if val < 0:
                raise ValueError(f"{field} não pode ser negativo: {val}")

@dataclass
class AuditDifference:
    field: str
    xml_value: str
    sefaz_value: str
    message: str

@dataclass
class AuditResultDTO:
    item_index: int
    product_code: str
    is_compliant: bool
    differences: list[AuditDifference]
