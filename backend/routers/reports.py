from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
import uuid
import aiofiles
from database import get_db
from models import Patient, PatientReport, User
from schemas import ReportResponse
from services.auth import get_current_user
from config import settings
import logging

router = APIRouter(prefix="/reports", tags=["Patient Reports"])
logger = logging.getLogger(__name__)

ALLOWED_TYPES = {
    "application/pdf", "image/jpeg", "image/png",
    "image/gif", "text/plain", "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}


@router.post("/{patient_id}/upload", response_model=ReportResponse, status_code=201)
async def upload_report(
    patient_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a report/document for a patient."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"File type not allowed: {file.content_type}")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"File too large (max {settings.MAX_UPLOAD_SIZE_MB}MB)")

    # Save file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    async with aiofiles.open(file_path, "wb") as out_file:
        await out_file.write(content)

    report = PatientReport(
        patient_id=patient_id,
        filename=unique_filename,
        original_filename=file.filename,
        file_size=len(content),
        content_type=file.content_type,
        description=description
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    logger.info(f"Report uploaded for patient {patient_id}: {file.filename}")
    return report


@router.get("/{patient_id}", response_model=list)
def list_patient_reports(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all reports for a patient."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    reports = db.query(PatientReport).filter(PatientReport.patient_id == patient_id).all()
    return [ReportResponse.model_validate(r) for r in reports]


@router.get("/download/{report_id}")
def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download a specific report."""
    report = db.query(PatientReport).filter(PatientReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    file_path = os.path.join(settings.UPLOAD_DIR, report.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=file_path,
        filename=report.original_filename,
        media_type=report.content_type
    )


@router.delete("/delete/{report_id}", status_code=204)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a report."""
    report = db.query(PatientReport).filter(PatientReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    file_path = os.path.join(settings.UPLOAD_DIR, report.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(report)
    db.commit()
    logger.info(f"Report deleted: ID {report_id}")
