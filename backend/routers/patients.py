from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas import PatientCreate, PatientUpdate, PatientResponse
from services.auth import get_current_user
from services import patient_service
from utils.response import success_response, paginated_response

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.post("")
def create_patient(
    data: PatientCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    patient = patient_service.create_patient(db, data, current_user)

    return success_response("Patient created", PatientResponse.model_validate(patient))


@router.get("")
def list_patients(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = patient_service.get_all_patients(db, page, page_size)

    items = [PatientResponse.model_validate(p) for p in result["items"]]

    return paginated_response("Patients retrieved", items, result["total"], page, page_size)


@router.put("/{patient_id}")
def update_patient(
    patient_id: int,
    data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    patient = patient_service.update_patient(db, patient_id, data)

    return success_response("Patient updated", PatientResponse.model_validate(patient))


@router.delete("/{patient_id}")
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    patient_service.delete_patient(db, patient_id)

    return success_response("Patient deleted")