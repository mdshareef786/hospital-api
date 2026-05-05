# ─── Feature 4: Service Layer for Appointments ────────────────────────────────
# Also handles Feature 3: double booking prevention + new statuses
import math
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from models import Appointment, Doctor, Patient, AppointmentStatus
from schemas import AppointmentCreate, AppointmentUpdate
from services.websocket_manager import ws_manager
import logging

logger = logging.getLogger(__name__)

# Time slot duration in minutes — no two appointments within this window
SLOT_DURATION_MINUTES = 30


def _check_double_booking(db: Session, doctor_id: int, appointment_date: datetime, exclude_id: int = None):
    """Prevent double booking: same doctor cannot have 2 appointments within 30 mins."""
    slot_start = appointment_date - timedelta(minutes=SLOT_DURATION_MINUTES)
    slot_end = appointment_date + timedelta(minutes=SLOT_DURATION_MINUTES)

    query = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date >= slot_start,
        Appointment.appointment_date <= slot_end,
        Appointment.status.notin_([AppointmentStatus.cancelled, AppointmentStatus.rejected])
    )
    if exclude_id:
        query = query.filter(Appointment.id != exclude_id)

    conflict = query.first()
    if conflict:
        raise HTTPException(
            status_code=400,
            detail=f"Doctor already has an appointment at {conflict.appointment_date.strftime('%Y-%m-%d %H:%M')}. Please choose a different time slot (min 30 min gap)."
        )


def get_all_appointments(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    doctor_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    status: Optional[AppointmentStatus] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort_by: str = "appointment_date",
    sort_order: str = "desc"
):
    query = db.query(Appointment).options(
        joinedload(Appointment.doctor),
        joinedload(Appointment.patient)
    )

    # Filtering
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if patient_id:
        query = query.filter(Appointment.patient_id == patient_id)
    if status:
        query = query.filter(Appointment.status == status)
    if date_from:
        query = query.filter(Appointment.appointment_date >= date_from)
    if date_to:
        query = query.filter(Appointment.appointment_date <= date_to)

    # Feature 5: Sorting
    sort_col = getattr(Appointment, sort_by, Appointment.appointment_date)
    query = query.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())

    total = query.count()
    appointments = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": appointments,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if page_size else 1
    }


def get_appointment_by_id(db: Session, appointment_id: int) -> Appointment:
    appointment = db.query(Appointment).options(
        joinedload(Appointment.doctor),
        joinedload(Appointment.patient)
    ).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


async def create_appointment(db: Session, data: AppointmentCreate) -> Appointment:
    # Validate doctor exists and is active
    doctor = db.query(Doctor).filter(Doctor.id == data.doctor_id, Doctor.is_active == True).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found or inactive")

    # Validate patient exists and is active
    patient = db.query(Patient).filter(Patient.id == data.patient_id, Patient.is_active == True).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found or inactive")

    # Feature 3: Prevent double booking
    _check_double_booking(db, data.doctor_id, data.appointment_date)

    appointment = Appointment(**data.model_dump(), status=AppointmentStatus.pending)
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    # Reload with relationships
    appointment = get_appointment_by_id(db, appointment.id)

    # Notify via WebSocket
    await ws_manager.notify_doctor(doctor.id, {
        "type": "new_appointment",
        "appointment_id": appointment.id,
        "patient_name": patient.name,
        "appointment_date": str(appointment.appointment_date),
        "message": f"New appointment request from {patient.name}"
    })
    await ws_manager.broadcast({
        "type": "appointment_update",
        "appointment_id": appointment.id,
        "message": f"New appointment booked: {doctor.name} ↔ {patient.name}"
    })

    logger.info(f"Appointment created: ID {appointment.id}")
    return appointment


async def update_appointment(db: Session, appointment_id: int, data: AppointmentUpdate) -> Appointment:
    appointment = get_appointment_by_id(db, appointment_id)

    if appointment.status in [AppointmentStatus.cancelled, AppointmentStatus.rejected]:
        raise HTTPException(status_code=400, detail="Cannot update a cancelled or rejected appointment")

    # If changing date, re-check double booking
    if data.appointment_date:
        _check_double_booking(db, appointment.doctor_id, data.appointment_date, exclude_id=appointment_id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(appointment, field, value)

    db.commit()

    if data.status:
        await ws_manager.broadcast({
            "type": "appointment_status_update",
            "appointment_id": appointment_id,
            "new_status": str(data.status),
            "message": f"Appointment #{appointment_id} is now {data.status}"
        })

    logger.info(f"Appointment updated: ID {appointment_id}")
    return get_appointment_by_id(db, appointment_id)


async def cancel_appointment(db: Session, appointment_id: int) -> Appointment:
    appointment = get_appointment_by_id(db, appointment_id)

    if appointment.status == AppointmentStatus.cancelled:
        raise HTTPException(status_code=400, detail="Appointment already cancelled")

    appointment.status = AppointmentStatus.cancelled
    db.commit()

    await ws_manager.broadcast({
        "type": "appointment_cancelled",
        "appointment_id": appointment_id,
        "message": f"Appointment #{appointment_id} has been cancelled"
    })

    logger.info(f"Appointment cancelled: ID {appointment_id}")
    return get_appointment_by_id(db, appointment_id)
