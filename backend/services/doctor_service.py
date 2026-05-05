import math
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models import Doctor
from schemas import DoctorCreate, DoctorUpdate
from utils.cache import cache

CACHE_KEY = "doctors"


def get_all_doctors(db: Session, page=1, page_size=10):
    cached = cache.get(CACHE_KEY)
    if cached:
        return cached

    query = db.query(Doctor)
    total = query.count()

    doctors = query.offset((page - 1) * page_size).limit(page_size).all()

    result = {
        "items": doctors,
        "total": total,
        "page": page,
        "page_size": page_size
    }

    cache.set(CACHE_KEY, result, 60)
    return result


def create_doctor(db: Session, data: DoctorCreate, current_user):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin allowed")

    doctor = Doctor(**data.model_dump())

    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    cache.delete(CACHE_KEY)

    return doctor


def update_doctor(db: Session, doctor_id: int, data: DoctorUpdate):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

    if not doctor:
        raise HTTPException(status_code=404, detail="Not found")

    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(doctor, k, v)

    db.commit()
    db.refresh(doctor)

    cache.delete(CACHE_KEY)

    return doctor


def delete_doctor(db: Session, doctor_id: int):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

    if not doctor:
        raise HTTPException(status_code=404, detail="Not found")

    db.delete(doctor)
    db.commit()

    cache.delete(CACHE_KEY)