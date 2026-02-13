from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import uuid
import sys
import os
import json
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.infrastructure.xml_reader import XMLReader
from src.services.audit_service import AuditService
from backend.core.database import get_db, engine, Base
from backend.core.models import Audit, AuditItem

# Create tables
Base.metadata.create_all(bind=engine)

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("uploads")
REPORTS_DIR = Path("reports")

def process_audit_background(audit_id: str, xml_path: Path):
    """Background task to process the audit."""
    db = next(get_db())
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    
    if not audit:
        return

    try:
        audit.status = "processing"
        audit.progress = 10
        audit.current_step = "Iniciando auditoria..."
        db.commit()
        
        service = AuditService()
        
        audit.progress = 30
        audit.current_step = "Processando itens..."
        db.commit()
        
        # This runs the full audit flow (Read -> Scrape -> Audit -> Report)
        report_path = service.process_audit(str(xml_path))
        
        # Move report
        final_report_path = REPORTS_DIR / f"{audit_id}_report.csv"
        if os.path.exists(report_path):
            shutil.move(report_path, final_report_path)
            
        audit.status = "completed"
        audit.progress = 100
        audit.current_step = "Concluído"
        audit.report_path = str(final_report_path)
        audit.completed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        logger.error(f"Error processing audit {audit_id}: {e}", exc_info=True)
        audit.status = "error"
        audit.error_message = str(e)
        db.commit()
    finally:
        db.close()

@router.post("/audit/upload")
async def upload_xml(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.xml'):
        raise HTTPException(400, "Apenas arquivos XML são aceitos")
    
    audit_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{audit_id}.xml"
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        reader = XMLReader()
        nfe_key, items = reader.parse(str(file_path))
        
        new_audit = Audit(
            id=audit_id,
            nfe_key=nfe_key,
            status="ready",
            progress=0,
            current_step="Upload concluído"
        )
        db.add(new_audit)
        db.commit()
        
        return {
            "audit_id": audit_id,
            "nfe_key": nfe_key,
            "total_items": len(items),
            "status": "ready"
        }
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(400, f"XML inválido: {str(e)}")

@router.post("/audit/start/{audit_id}")
async def start_audit(audit_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(404, "Auditoria não encontrada")
    
    xml_path = UPLOAD_DIR / f"{audit_id}.xml"
    if not xml_path.exists():
        raise HTTPException(404, "Arquivo XML não encontrado")
        
    background_tasks.add_task(process_audit_background, audit_id, xml_path)
    
    return {"status": "processing", "audit_id": audit_id}

@router.get("/audit/status/{audit_id}")
async def get_status(audit_id: str, db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(404, "Auditoria não encontrada")
    
    return {
        "audit_id": audit.id,
        "status": audit.status,
        "progress": audit.progress,
        "step": audit.current_step,
        "error": audit.error_message,
        "report_path": audit.report_path
    }

@router.get("/audit/download/{audit_id}")
async def download_report(audit_id: str):
    report_path = REPORTS_DIR / f"{audit_id}_report.csv"
    if not report_path.exists():
        raise HTTPException(404, "Relatório não encontrado")
    
    return FileResponse(
        report_path,
        media_type="text/csv",
        filename=f"auditoria_{audit_id}.csv"
    )
