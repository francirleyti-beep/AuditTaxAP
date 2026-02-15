from datetime import datetime
from dataclasses import dataclass, field
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
    product_description: str  # [NEW] xProd
    ncm: str
    cest: str
    cfop: str
    cst: str
    quantity: Decimal         # [NEW] qCom
    unit_price: Decimal       # [NEW] vUnCom
    amount_total: Decimal     # vProd
    tax_base: Decimal
    tax_rate: Decimal
    tax_value: Decimal
    mva_percent: Decimal
    is_suframa_benefit: bool
    # Campos específicos da SEFAZ (opcionais, preenchidos pelo ItemExtractor)
    sefaz_tax_value: Decimal = field(default_factory=lambda: Decimal("0.00"))
    sefaz_mva_percent: Decimal = field(default_factory=lambda: Decimal("0.00"))
    sefaz_benefit_value: Decimal = field(default_factory=lambda: Decimal("0.00"))

    def __post_init__(self):
        """Validações básicas após inicialização."""
        if self.origin not in ['XML', 'SEFAZ']:
            raise ValueError(f"Origin inválida: {self.origin}")
        
        if self.item_index <= 0:
            raise ValueError(f"item_index deve ser positivo: {self.item_index}")
            
        # Validar valores monetários não negativos
        monetary_fields = ['quantity', 'unit_price', 'amount_total', 'tax_base', 'tax_rate', 'tax_value', 'mva_percent',
                          'sefaz_tax_value', 'sefaz_mva_percent', 'sefaz_benefit_value']
        for field in monetary_fields:
            val = getattr(self, field)
            if val < 0:
                raise ValueError(f"{field} não pode ser negativo: {val}")

@dataclass
class InvoiceDTO:
    """
    Data Transfer Object que representa a Nota Fiscal completa (Cabeçalho + Itens).
    Usado para validações de consistência interna (Totais x Soma Itens).
    """
    access_key: str
    number: int
    series: int
    issue_date: datetime
    # Emitente
    emitter_name: str
    emitter_cnpj: str
    emitter_city: str
    # Destinatário
    recipient_name: str
    recipient_doc: str # CPF ou CNPJ
    # Totais
    total_products: Decimal # vProd (Total dos produtos)
    total_invoice: Decimal  # vNF (Total da Nota)
    total_icms: Decimal     # vICMS (Total ICMS)
    # Transporte e Protocolo
    freight_mode: str       # modFrete
    protocol_number: str    # nProt
    protocol_date: datetime # dhRecbto
    
    items: list[FiscalItemDTO] = field(default_factory=list)

    def __iter__(self):
        """Allows unpacking as (access_key, items) for backward compatibility."""
        yield self.access_key
        yield self.items

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
