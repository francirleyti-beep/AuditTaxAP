from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Audit(Base):
    __tablename__ = "audits"

    id = Column(String, primary_key=True, index=True)
    nfe_key = Column(String, index=True)
    status = Column(String, default="pending")  # pending, processing, completed, error
    progress = Column(Integer, default=0)
    current_step = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    result_summary = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)
    report_path = Column(String, nullable=True)

    items = relationship("AuditItem", back_populates="audit")

class AuditItem(Base):
    __tablename__ = "audit_items"

    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(String, ForeignKey("audits.id"))
    item_index = Column(Integer)
    product_code = Column(String)
    product_name = Column(String)
    status = Column(String) # compliant, divergent
    issues = Column(JSON) # List of divergence messages

    audit = relationship("Audit", back_populates="items")
