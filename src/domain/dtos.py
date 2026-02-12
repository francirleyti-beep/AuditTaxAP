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
