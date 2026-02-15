import os
import shutil
from pathlib import Path
from datetime import datetime
import decimal
from decimal import Decimal
from celery import Celery
from sqlalchemy.orm import Session
import redis
import json

# Import project modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.services.audit_service import AuditService
from backend.core.database import SessionLocal
from backend.core.models import Audit, AuditItem

# Configure Celery
celery_app = Celery(
    "audit_worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
)

# Redis client for publishing updates
redis_client = redis.Redis.from_url(os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"))

# Optional configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
)

REPORTS_DIR = Path("reports")

@celery_app.task(bind=True, name="process_audit_task")
def process_audit_task(self, audit_id: str, xml_path_str: str):
    """
    Celery task to process the audit.
    Replaces the previous process_audit_background function.
    """
    db: Session = SessionLocal()
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    
    if not audit:
        db.close()
        return "Audit not found"

    def publish_update(status, progress, step, error=None, result=None):
        message = {
            "audit_id": audit_id,
            "status": status,
            "progress": progress,
            "step": step,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        if result:
            message["result"] = result
            
        redis_client.publish(f"audit_updates:{audit_id}", json.dumps(message))

    try:
        # Update status to processing
        audit.status = "processing"
        audit.progress = 10
        audit.current_step = "Starting audit (Worker)..."
        db.commit()
        publish_update("processing", 10, "Starting audit (Worker)...")
        
        service = AuditService()
        
        audit.progress = 30
        audit.current_step = "Processing items..."
        db.commit()
        publish_update("processing", 30, "Processing items...")
        
        audit.progress = 30
        audit.current_step = "Processing items..."
        db.commit()
        publish_update("processing", 30, "Processing items...")
        
        # Run audit
        # Retorna: report_path, audit_results, consistency_errors, invoice_dto
        report_path, audit_results, consistency_errors, invoice_dto = service.process_audit(xml_path_str)
        
        # Helper para serializar objetos (Decimal -> float/str, Datetime -> isoformat)
        def serialize_val(val):
            if isinstance(val, decimal.Decimal):
                return float(val) # JSON suporta float, frontend facilita. Se precisar precisão exata, usar str.
            if isinstance(val, datetime):
                return val.isoformat()
            return val

        def to_dict(obj):
            if hasattr(obj, "__dict__"):
                return {k: serialize_val(v) for k, v in obj.__dict__.items() if not k.startswith('_')}
            return obj

        # Save Invoice Header (excluindo itens para não duplicar muito dado)
        header_data = {
            "access_key": invoice_dto.access_key,
            "number": invoice_dto.number,
            "series": invoice_dto.series,
            "issue_date": serialize_val(invoice_dto.issue_date),
            "emitter_name": invoice_dto.emitter_name,
            "emitter_cnpj": invoice_dto.emitter_cnpj,
            "recipient_name": invoice_dto.recipient_name,
            "recipient_doc": invoice_dto.recipient_doc,
            "total_products": serialize_val(invoice_dto.total_products),
            "total_invoice": serialize_val(invoice_dto.total_invoice),
            "total_icms": serialize_val(invoice_dto.total_icms),
            "protocol_number": invoice_dto.protocol_number
        }
        audit.invoice_header = header_data
        
        # Save Consistency Errors
        audit.consistency_errors = [to_dict(err) for err in consistency_errors]
        
        # Save results to DB
        # Criar mapa de itens por índice para acesso rápido
        items_map = {item.item_index: item for item in invoice_dto.items}

        for res in audit_results:
            # Encontrar detalhes do item original
            fiscal_item = items_map.get(res.item_index)
            details_json = to_dict(fiscal_item) if fiscal_item else {}
            
            item = AuditItem(
                audit_id=audit_id,
                item_index=res.item_index,
                product_code=res.product_code,
                product_name=fiscal_item.product_description if fiscal_item else f"ITEM {res.item_index}", 
                status="compliant" if res.is_compliant else "divergent",
                issues=[d.message for d in res.differences],
                details=details_json
            )
            db.add(item)
        
        # Move report
        final_report_path = REPORTS_DIR / f"{audit_id}_report.csv"
        # Ensure reports dir exists
        REPORTS_DIR.mkdir(exist_ok=True)
        
        if os.path.exists(report_path):
            shutil.move(report_path, final_report_path)
            
        audit.status = "completed"
        audit.progress = 100
        audit.current_step = "Completed"
        audit.report_path = str(final_report_path)
        audit.completed_at = datetime.utcnow()
        audit.result_summary = {
            "total": len(audit_results),
            "compliant": len([r for r in audit_results if r.is_compliant]),
            "divergent": len([r for r in audit_results if not r.is_compliant]),
            "consistency_issues": len(consistency_errors)
        }
        db.commit()
        publish_update("completed", 100, "Completed", result=audit.result_summary)
        return "Success"
        
    except Exception as e:
        print(f"Error processing audit {audit_id}: {e}")
        audit.status = "error"
        audit.error_message = str(e)
        db.commit()
        publish_update("error", 0, "Error", error=str(e))
        # Re-raise to let Celery know it failed (triggers retry if configured)
        raise e
    finally:
        db.close()
