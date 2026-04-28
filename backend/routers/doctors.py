from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from database import get_db
from models import Doctor, User
from schemas import DoctorCreate, DoctorUpdate, DoctorResponse
from services.auth import get_current_user
import logging
import math

router = APIRouter(prefix="/doctors", tags=["Doctors"])
logger = logging.getLogger(__name__)


@router.post("", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
def create_doctor(
    doctor_data: DoctorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new doctor."""
    if db.query(Doctor).filter(Doctor.email == doctor_data.email).first():
        raise HTTPException(status_code=400, detail="Doctor with this email already exists")

    doctor = Doctor(**doctor_data.model_dump())
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    logger.info(f"Doctor created: {doctor.name} (ID: {doctor.id})")
    return doctor


@router.get("", response_model=dict)
def list_doctors(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    specialization: Optional[str] = Query(None, description="Filter by specialization"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all doctors with pagination and filtering."""
    query = db.query(Doctor)

    if specialization:
        query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))
    if is_active is not None:
        query = query.filter(Doctor.is_active == is_active)
    if search:
        query = query.filter(Doctor.name.ilike(f"%{search}%"))

    total = query.count()
    doctors = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size),
        "items": [DoctorResponse.model_validate(d) for d in doctors]
    }


@router.get("/{doctor_id}", response_model=DoctorResponse)
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific doctor by ID."""
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


@router.put("/{doctor_id}", response_model=DoctorResponse)
def update_doctor(
    doctor_id: int,
    doctor_data: DoctorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a doctor's information."""
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    if doctor_data.email and doctor_data.email != doctor.email:
        if db.query(Doctor).filter(Doctor.email == doctor_data.email).first():
            raise HTTPException(status_code=400, detail="Email already in use")

    update_data = doctor_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(doctor, field, value)

    db.commit()
    db.refresh(doctor)
    logger.info(f"Doctor updated: ID {doctor_id}")
    return doctor


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a doctor."""
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    db.delete(doctor)
    db.commit()
    logger.info(f"Doctor deleted: ID {doctor_id}")


@router.patch("/{doctor_id}/toggle-status", response_model=DoctorResponse)
def toggle_doctor_status(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activate or deactivate a doctor."""
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor.is_active = not doctor.is_active
    db.commit()
    db.refresh(doctor)
    status_str = "activated" if doctor.is_active else "deactivated"
    logger.info(f"Doctor {doctor_id} {status_str}")
    return doctor
