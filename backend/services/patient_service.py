# ─── Feature 4: Service Layer for Patients ────────────────────────────────────
import math
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models import Patient
from schemas import PatientCreate, PatientUpdate
import logging

logger = logging.getLogger(__name__)


def get_all_patients(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):
    query = db.query(Patient)

    if search:
        query = query.filter(
            Patient.name.ilike(f"%{search}%") |
            Patient.phone.ilike(f"%{search}%")
        )
    if is_active is not None:
        query = query.filter(Patient.is_active == is_active)

    # Feature 5: Sorting
    sort_col = getattr(Patient, sort_by, Patient.created_at)
    query = query.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())

    total = query.count()
    patients = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": patients,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if page_size else 1
    }


def get_patient_by_id(db: Session, patient_id: int) -> Patient:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


def create_patient(db: Session, data: PatientCreate) -> Patient:
    patient = Patient(**data.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    logger.info(f"Patient created: {patient.name}")
    return patient


def update_patient(db: Session, patient_id: int, data: PatientUpdate) -> Patient:
    patient = get_patient_by_id(db, patient_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    logger.info(f"Patient updated: ID {patient_id}")
    return patient


def delete_patient(db: Session, patient_id: int):
    patient = get_patient_by_id(db, patient_id)
    db.delete(patient)
    db.commit()
    logger.info(f"Patient deleted: ID {patient_id}")
