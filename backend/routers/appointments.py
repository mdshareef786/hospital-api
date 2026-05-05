from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from database import get_db
from models import UserRole, AppointmentStatus
from schemas import AppointmentCreate, AppointmentUpdate, AppointmentResponse
from services.auth import get_current_user
from services.auth_service import require_roles
from services import appointment_service
from utils.response import success_response, paginated_response

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("", status_code=201)
async def create_appointment(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    appointment = await appointment_service.create_appointment(db, data)
    return success_response("Appointment booked", AppointmentResponse.model_validate(appointment))


@router.get("")
def list_appointments(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    doctor_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    status: Optional[AppointmentStatus] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort_by: str = Query("appointment_date", enum=["appointment_date", "created_at", "status"]),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = appointment_service.get_all_appointments(
        db, page, page_size, doctor_id, patient_id, status, date_from, date_to, sort_by, sort_order
    )
    items = [AppointmentResponse.model_validate(a) for a in result["items"]]
    return paginated_response("Appointments retrieved", items, result["total"], page, page_size)


@router.get("/{appointment_id}")
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    appointment = appointment_service.get_appointment_by_id(db, appointment_id)
    return success_response("Appointment retrieved", AppointmentResponse.model_validate(appointment))


@router.put("/{appointment_id}")
async def update_appointment(
    appointment_id: int,
    data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user=require_roles(UserRole.admin, UserRole.doctor)
):
    appointment = await appointment_service.update_appointment(db, appointment_id, data)
    return success_response("Appointment updated", AppointmentResponse.model_validate(appointment))


@router.patch("/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    appointment = await appointment_service.cancel_appointment(db, appointment_id)
    return success_response("Appointment cancelled", AppointmentResponse.model_validate(appointment))
