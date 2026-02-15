from src.domain.dtos import InvoiceDTO
from decimal import Decimal
from datetime import datetime

dto = InvoiceDTO(
    access_key="123", items=[], number=1, series=1, issue_date=datetime.now(),
    emitter_name="A", emitter_cnpj="B", emitter_city="C",
    recipient_name="D", recipient_doc="E",
    total_products=Decimal(10), total_invoice=Decimal(10), total_icms=Decimal(0),
    freight_mode="0", protocol_number="123", protocol_date=datetime.now()
)

try:
    key, items = dto
    print(f"SUCCESS: Unpacked key={key}, items={items}")
    print(f"DTO Attributes: key={dto.access_key}, items={dto.items}")
except Exception as e:
    print(f"FAILURE: {e}")
