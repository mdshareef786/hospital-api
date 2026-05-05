import math
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models import Patient
from schemas import PatientCreate, PatientUpdate


def get_all_patients(db: Session, page=1, page_size=10):
    query = db.query(Patient)

    total = query.count()
    patients = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": patients,
        "total": total,
        "page": page,
        "page_size": page_size
    }


def create_patient(db: Session, data: PatientCreate, current_user):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patient allowed")

    patient = Patient(**data.model_dump(), user_id=current_user.id)

    db.add(patient)
    db.commit()
    db.refresh(patient)

    return patient


def update_patient(db: Session, patient_id: int, data: PatientUpdate):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Not found")

    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(patient, k, v)

    db.commit()
    db.refresh(patient)

    return patient


def delete_patient(db: Session, patient_id: int):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Not found")

    db.delete(patient)
    db.commit()