from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends, WebSocket
from fastapi_limiter.depends import RateLimiter
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

from backend.api.celery_worker import process_audit_task
from backend.api.websockets import manager

MAX_UPLOAD_SIZE = 50 * 1024 * 1024 # 50MB

async def validate_upload_size(file: UploadFile = File(...)):
    # Simple check, but for real streaming generic limitation better use middleware or nginx
    # Here we check content-length header if available or read chunk
    return file

@router.post("/audit/upload", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def upload_xml(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.xml'):
        raise HTTPException(400, "Apenas arquivos XML são aceitos")
    
    audit_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{audit_id}.xml"
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        reader = XMLReader()
        invoice_dto = reader.parse(str(file_path))
        print(f"DEBUG: Parsed InvoiceDTO: {invoice_dto}", flush=True)
        nfe_key = invoice_dto.access_key
        items = invoice_dto.items
        
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
async def start_audit(audit_id: str, db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(404, "Auditoria não encontrada")
    
    xml_path = UPLOAD_DIR / f"{audit_id}.xml"
    if not xml_path.exists():
        raise HTTPException(404, "Arquivo XML não encontrado")
        
    # Trigger Celery Task
    process_audit_task.delay(audit_id, str(xml_path))
    
    return {"status": "queued", "audit_id": audit_id}

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

@router.get("/audit/{audit_id}/results")
async def get_audit_results(audit_id: str, db: Session = Depends(get_db)):
    """Retorna os resultados detalhados da auditoria."""
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(404, "Auditoria não encontrada")
        
    items = db.query(AuditItem).filter(AuditItem.audit_id == audit_id).order_by(AuditItem.item_index).all()
    
    return {
        "audit_id": audit.id,
        "summary": audit.result_summary,
        "invoice_header": audit.invoice_header,
        "consistency_errors": audit.consistency_errors,
        "is_fully_reviewed": bool(audit.is_fully_reviewed), # [NEW]
        "items": [
            {
                "item_index": item.item_index,
                "product_code": item.product_code,
                "product_name": item.product_name,
                "status": item.status,
                "issues": item.issues,
                "is_reviewed": bool(item.is_reviewed),   # [NEW]
                "details": item.details
            }
            for item in items
        ]
    }

@router.websocket("/ws/audit/{audit_id}")
async def websocket_endpoint(websocket: WebSocket, audit_id: str):
    await manager.connect(websocket)
    await manager.stream_audit_updates(websocket, audit_id)

@router.get("/audits")
async def list_audits(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Listar histórico de auditorias."""
    audits = db.query(Audit).order_by(Audit.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": a.id,
            "nfe_key": a.nfe_key,
            "status": a.status,
            "created_at": a.created_at,
            "completed_at": a.completed_at,
            "summary": a.result_summary,
            "is_fully_reviewed": bool(a.is_fully_reviewed)
        }
        for a in audits
    ]

@router.delete("/audit/{audit_id}")
async def delete_audit(audit_id: str, db: Session = Depends(get_db)):
    """Remove uma auditoria, seus itens e arquivos associados."""
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(404, "Auditoria não encontrada")
    
    # 1. Remover arquivos
    xml_path = UPLOAD_DIR / f"{audit_id}.xml"
    report_path = REPORTS_DIR / f"{audit_id}_report.csv"
    
    if xml_path.exists(): xml_path.unlink()
    if report_path.exists(): report_path.unlink()
    
    # 2. Remover itens (Cascata manual caso não esteja no model)
    db.query(AuditItem).filter(AuditItem.audit_id == audit_id).delete()
    
    # 3. Remover auditoria
    db.delete(audit)
    db.commit()
    
    return {"status": "success", "message": "Auditoria excluída"}

@router.post("/audit/{audit_id}/retry")
async def retry_audit(audit_id: str, db: Session = Depends(get_db)):
    """Reinicia uma auditoria existente."""
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(404, "Auditoria não encontrada")
    
    xml_path = UPLOAD_DIR / f"{audit_id}.xml"
    if not xml_path.exists():
        raise HTTPException(400, "Arquivo XML original não encontrado para re-auditoria")
    
    # Resetar status
    audit.status = "ready"
    audit.progress = 0
    audit.current_step = "Reiniciando..."
    audit.error_message = None
    
    # Limpar itens anteriores
    db.query(AuditItem).filter(AuditItem.audit_id == audit_id).delete()
    db.commit()
    
    # Trigger Celery Task
    process_audit_task.delay(audit_id, str(xml_path))
    
    return {"status": "queued", "audit_id": audit_id}

@router.patch("/audit/item/{audit_id}/{item_index}/review")
async def toggle_item_review(audit_id: str, item_index: int, reviewed: bool, db: Session = Depends(get_db)):
    """Marca ou desmarca um item como conferido."""
    item = db.query(AuditItem).filter(
        AuditItem.audit_id == audit_id, 
        AuditItem.item_index == item_index
    ).first()
    
    if not item:
        raise HTTPException(404, "Item não encontrado")
    
    item.is_reviewed = 1 if reviewed else 0
    db.commit()
    return {"status": "success", "is_reviewed": bool(item.is_reviewed)}

@router.post("/audit/{audit_id}/finalize")
async def finalize_audit_review(audit_id: str, db: Session = Depends(get_db)):
    """Finaliza a auditoria se todos os itens estiverem conferidos."""
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(404, "Auditoria não encontrada")
    
    # Verificar se todos os itens estão marcados
    total_items = db.query(AuditItem).filter(AuditItem.audit_id == audit_id).count()
    reviewed_items = db.query(AuditItem).filter(AuditItem.audit_id == audit_id, AuditItem.is_reviewed == 1).count()
    
    if reviewed_items < total_items:
        raise HTTPException(400, f"Não é possível finalizar: {total_items - reviewed_items} itens ainda não foram conferidos.")
    
    audit.is_fully_reviewed = 1
    db.commit()
    return {"status": "success", "is_fully_reviewed": True}
