from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models import UserRole
from schemas import DoctorCreate, DoctorUpdate, DoctorResponse
from services.auth import get_current_user
from services.auth_service import require_roles
from services import doctor_service
from utils.response import success_response, paginated_response

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.post("")
def create_doctor(
    data: DoctorCreate,
    db: Session = Depends(get_db),
    current_user=require_roles(UserRole.admin)
):
    doctor = doctor_service.create_doctor(db, data, current_user)
    return success_response("Doctor created", DoctorResponse.model_validate(doctor))


@router.get("")
def list_doctors(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = doctor_service.get_all_doctors(db, page, page_size)

    items = [DoctorResponse.model_validate(d) for d in result["items"]]

    return paginated_response("Doctors retrieved", items, result["total"], page, page_size)


@router.put("/{doctor_id}")
def update_doctor(
    doctor_id: int,
    data: DoctorUpdate,
    db: Session = Depends(get_db),
    current_user=require_roles(UserRole.admin)
):
    doctor = doctor_service.update_doctor(db, doctor_id, data)
    return success_response("Doctor updated", DoctorResponse.model_validate(doctor))


@router.delete("/{doctor_id}")
def delete_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user=require_roles(UserRole.admin)
):
    doctor_service.delete_doctor(db, doctor_id)
    return success_response("Doctor deleted")