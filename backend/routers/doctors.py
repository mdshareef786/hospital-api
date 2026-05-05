from fastapi import APIRouter, Depends, status, Query
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


@router.post("", status_code=status.HTTP_201_CREATED)
def create_doctor(
    data: DoctorCreate,
    db: Session = Depends(get_db),
    current_user=require_roles(UserRole.admin)
):
    doctor = doctor_service.create_doctor(db, data)
    return success_response("Doctor created", DoctorResponse.model_validate(doctor))


@router.get("")
def list_doctors(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    specialization: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort_by: str = Query("created_at", enum=["name", "specialization", "created_at"]),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = doctor_service.get_all_doctors(db, page, page_size, search, specialization, is_active, sort_by, sort_order)
    items = [DoctorResponse.model_validate(d) for d in result["items"]]
    return paginated_response("Doctors retrieved", items, result["total"], page, page_size)


@router.get("/{doctor_id}")
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    doctor = doctor_service.get_doctor_by_id(db, doctor_id)
    return success_response("Doctor retrieved", DoctorResponse.model_validate(doctor))


@router.put("/{doctor_id}")
def update_doctor(
    doctor_id: int,
    data: DoctorUpdate,
    db: Session = Depends(get_db),
    current_user=require_roles(UserRole.admin)
):
    doctor = doctor_service.update_doctor(db, doctor_id, data)
    return success_response("Doctor updated", DoctorResponse.model_validate(doctor))


@router.delete("/{doctor_id}", status_code=status.HTTP_200_OK)
def delete_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user=require_roles(UserRole.admin)
):
    doctor_service.delete_doctor(db, doctor_id)
    return success_response("Doctor deleted")


@router.patch("/{doctor_id}/toggle-status")
def toggle_status(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user=require_roles(UserRole.admin)
):
    doctor = doctor_service.toggle_doctor_status(db, doctor_id)
    return success_response(
        f"Doctor {'activated' if doctor.is_active else 'deactivated'}",
        DoctorResponse.model_validate(doctor)
    )
