from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import UserRole
from schemas import PatientCreate, PatientUpdate, PatientResponse
from services.auth import get_current_user
from services.auth_service import require_roles
from services import patient_service
from utils.response import success_response, paginated_response

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_patient(
    data: PatientCreate,
    db: Session = Depends(get_db),
    current_user=require_roles(UserRole.admin, UserRole.doctor)
):
    patient = patient_service.create_patient(db, data)
    return success_response("Patient created", PatientResponse.model_validate(patient))


@router.get("")
def list_patients(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort_by: str = Query("created_at", enum=["name", "age", "created_at"]),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = patient_service.get_all_patients(db, page, page_size, search, is_active, sort_by, sort_order)
    items = [PatientResponse.model_validate(p) for p in result["items"]]
    return paginated_response("Patients retrieved", items, result["total"], page, page_size)


@router.get("/{patient_id}")
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    patient = patient_service.get_patient_by_id(db, patient_id)
    return success_response("Patient retrieved", PatientResponse.model_validate(patient))


@router.put("/{patient_id}")
def update_patient(
    patient_id: int,
    data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user=require_roles(UserRole.admin, UserRole.doctor)
):
    patient = patient_service.update_patient(db, patient_id, data)
    return success_response("Patient updated", PatientResponse.model_validate(patient))


@router.delete("/{patient_id}")
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user=require_roles(UserRole.admin)
):
    patient_service.delete_patient(db, patient_id)
    return success_response("Patient deleted")
