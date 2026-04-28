from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import datetime
from database import get_db
from models import Appointment, Doctor, Patient, User, AppointmentStatus
from schemas import AppointmentCreate, AppointmentUpdate, AppointmentResponse
from services.auth import get_current_user
from services.websocket_manager import ws_manager
import logging
import math

router = APIRouter(prefix="/appointments", tags=["Appointments"])
logger = logging.getLogger(__name__)


async def notify_new_appointment(doctor_id: int, appointment_id: int, patient_name: str, appointment_date: str):
    """Background task to notify doctor of new appointment via WebSocket."""
    message = {
        "type": "new_appointment",
        "appointment_id": appointment_id,
        "patient_name": patient_name,
        "appointment_date": appointment_date,
        "message": f"New appointment booked by {patient_name} on {appointment_date}"
    }
    await ws_manager.notify_doctor(doctor_id, message)
    await ws_manager.broadcast({**message, "type": "appointment_update"})


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appt_data: AppointmentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new appointment."""
    doctor = db.query(Doctor).filter(Doctor.id == appt_data.doctor_id, Doctor.is_active == True).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found or inactive")

    patient = db.query(Patient).filter(Patient.id == appt_data.patient_id, Patient.is_active == True).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found or inactive")

    from datetime import timezone
    if appt_data.appointment_date.replace(tzinfo=None) < datetime.utcnow().replace(tzinfo=None):
        raise HTTPException(status_code=400, detail="Appointment date must be in the future")

    appointment = Appointment(**appt_data.model_dump())
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    # Load relationships
    appointment = db.query(Appointment).options(
        joinedload(Appointment.doctor),
        joinedload(Appointment.patient)
    ).filter(Appointment.id == appointment.id).first()

    # Trigger WebSocket notification as background task
    background_tasks.add_task(
        notify_new_appointment,
        doctor_id=doctor.id,
        appointment_id=appointment.id,
        patient_name=patient.name,
        appointment_date=str(appointment.appointment_date)
    )

    logger.info(f"Appointment created: ID {appointment.id}, Doctor {doctor.id}, Patient {patient.id}")
    return appointment


@router.get("", response_model=dict)
def list_appointments(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    doctor_id: Optional[int] = Query(None),
    patient_id: Optional[int] = Query(None),
    status: Optional[AppointmentStatus] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List appointments with filters."""
    query = db.query(Appointment).options(
        joinedload(Appointment.doctor),
        joinedload(Appointment.patient)
    )

    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if patient_id:
        query = query.filter(Appointment.patient_id == patient_id)
    if status:
        query = query.filter(Appointment.status == status)

    total = query.count()
    appointments = query.order_by(Appointment.appointment_date.desc()) \
                        .offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size),
        "items": [AppointmentResponse.model_validate(a) for a in appointments]
    }


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific appointment."""
    appointment = db.query(Appointment).options(
        joinedload(Appointment.doctor),
        joinedload(Appointment.patient)
    ).filter(Appointment.id == appointment_id).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    appt_data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an appointment."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment.status == AppointmentStatus.cancelled:
        raise HTTPException(status_code=400, detail="Cannot update a cancelled appointment")

    update_data = appt_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(appointment, field, value)

    db.commit()

    # Notify about status update
    if appt_data.status:
        await ws_manager.broadcast({
            "type": "appointment_status_update",
            "appointment_id": appointment_id,
            "new_status": str(appt_data.status),
            "message": f"Appointment #{appointment_id} status changed to {appt_data.status}"
        })

    appointment = db.query(Appointment).options(
        joinedload(Appointment.doctor),
        joinedload(Appointment.patient)
    ).filter(Appointment.id == appointment_id).first()

    logger.info(f"Appointment updated: ID {appointment_id}")
    return appointment


@router.patch("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel an appointment."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment.status == AppointmentStatus.cancelled:
        raise HTTPException(status_code=400, detail="Appointment already cancelled")

    appointment.status = AppointmentStatus.cancelled
    db.commit()

    await ws_manager.broadcast({
        "type": "appointment_cancelled",
        "appointment_id": appointment_id,
        "message": f"Appointment #{appointment_id} has been cancelled"
    })

    appointment = db.query(Appointment).options(
        joinedload(Appointment.doctor),
        joinedload(Appointment.patient)
    ).filter(Appointment.id == appointment_id).first()

    logger.info(f"Appointment cancelled: ID {appointment_id}")
    return appointment
