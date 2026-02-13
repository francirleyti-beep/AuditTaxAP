import os
import shutil
from pathlib import Path
from datetime import datetime
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
        
        # Run audit
        report_path, audit_results = service.process_audit(xml_path_str)
        
        # Save results to DB
        for res in audit_results:
            item = AuditItem(
                audit_id=audit_id,
                item_index=res.item_index,
                product_code=res.product_code,
                product_name=f"ITEM {res.item_index}", 
                status="compliant" if res.is_compliant else "divergent",
                issues=[d.message for d in res.differences]
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
            "divergent": len([r for r in audit_results if not r.is_compliant])
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
