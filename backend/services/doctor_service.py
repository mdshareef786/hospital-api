# ─── Feature 4: Service Layer for Doctors ─────────────────────────────────────
import math
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models import Doctor
from schemas import DoctorCreate, DoctorUpdate
from utils.cache import cache
import logging

logger = logging.getLogger(__name__)
CACHE_KEY = "doctors_list"


def get_all_doctors(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    search: Optional[str] = None,
    specialization: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):
    # Feature 8: Try cache only for default unfiltered requests
    if not search and not specialization and is_active is None and page == 1 and sort_by == "created_at":
        cached = cache.get(CACHE_KEY)
        if cached:
            return cached

    query = db.query(Doctor)

    # Filtering
    if search:
        query = query.filter(
            Doctor.name.ilike(f"%{search}%") |
            Doctor.specialization.ilike(f"%{search}%")
        )
    if specialization:
        query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))
    if is_active is not None:
        query = query.filter(Doctor.is_active == is_active)

    # Feature 5: Sorting
    sort_col = getattr(Doctor, sort_by, Doctor.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    total = query.count()
    doctors = query.offset((page - 1) * page_size).limit(page_size).all()

    result = {
        "items": doctors,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if page_size else 1
    }

    # Store in cache for default requests
    if not search and not specialization and is_active is None and page == 1:
        cache.set(CACHE_KEY, result, ttl_seconds=60)

    return result


def get_doctor_by_id(db: Session, doctor_id: int) -> Doctor:
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


def create_doctor(db: Session, data: DoctorCreate) -> Doctor:
    if db.query(Doctor).filter(Doctor.email == data.email).first():
        raise HTTPException(status_code=400, detail="Doctor with this email already exists")
    doctor = Doctor(**data.model_dump())
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    cache.delete(CACHE_KEY)  # Invalidate cache
    logger.info(f"Doctor created: {doctor.name}")
    return doctor


def update_doctor(db: Session, doctor_id: int, data: DoctorUpdate) -> Doctor:
    doctor = get_doctor_by_id(db, doctor_id)
    if data.email and data.email != doctor.email:
        if db.query(Doctor).filter(Doctor.email == data.email).first():
            raise HTTPException(status_code=400, detail="Email already in use")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(doctor, field, value)
    db.commit()
    db.refresh(doctor)
    cache.delete(CACHE_KEY)
    logger.info(f"Doctor updated: ID {doctor_id}")
    return doctor


def delete_doctor(db: Session, doctor_id: int):
    doctor = get_doctor_by_id(db, doctor_id)
    db.delete(doctor)
    db.commit()
    cache.delete(CACHE_KEY)
    logger.info(f"Doctor deleted: ID {doctor_id}")


def toggle_doctor_status(db: Session, doctor_id: int) -> Doctor:
    doctor = get_doctor_by_id(db, doctor_id)
    doctor.is_active = not doctor.is_active
    db.commit()
    db.refresh(doctor)
    cache.delete(CACHE_KEY)
    logger.info(f"Doctor {doctor_id} {'activated' if doctor.is_active else 'deactivated'}")
    return doctor
