from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Generic, TypeVar
from datetime import datetime
from enum import Enum


# ─── Enums ────────────────────────────────────────────────────────────────────

class UserRole(str, Enum):
    admin = "admin"
    doctor = "doctor"
    patient = "patient"


class AppointmentStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    completed = "completed"
    cancelled = "cancelled"


# ─── Standard API Response ─────────────────────────────────────────────────────

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    status: str
    message: str
    data: Optional[T]


# ─── Auth Schemas ──────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)


# ─── Doctor Schemas ────────────────────────────────────────────────────────────

class DoctorBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    specialization: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = None


class DoctorCreate(DoctorBase):
    user_id: int   # 🔥 important for linking user


class DoctorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    specialization: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class DoctorResponse(DoctorBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Patient Schemas ───────────────────────────────────────────────────────────

class PatientBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., gt=0, lt=150)
    phone: str = Field(..., min_length=7, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None


class PatientCreate(PatientBase):
    user_id: int   # 🔥 important


class PatientUpdate(BaseModel):
    name: Optional[str]
    age: Optional[int]
    phone: Optional[str]
    email: Optional[EmailStr]
    address: Optional[str]
    is_active: Optional[bool]


class PatientResponse(PatientBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Appointment Schemas ───────────────────────────────────────────────────────

class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    appointment_date: datetime
    notes: Optional[str] = None

    @validator("appointment_date")
    def validate_future_date(cls, value):
        if value < datetime.utcnow():
            raise ValueError("Appointment must be in the future")
        return value


class AppointmentUpdate(BaseModel):
    appointment_date: Optional[datetime]
    status: Optional[AppointmentStatus]
    notes: Optional[str]


class AppointmentResponse(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    appointment_date: datetime
    status: AppointmentStatus
    notes: Optional[str]
    created_at: datetime

    doctor: Optional[DoctorResponse]
    patient: Optional[PatientResponse]

    class Config:
        from_attributes = True


# ─── Pagination Schema ─────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    page: int
    page_size: int
    data: List[T]


# ─── Report Schemas ────────────────────────────────────────────────────────────

class ReportResponse(BaseModel):
    id: int
    patient_id: int
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    description: Optional[str]
    uploaded_at: datetime

    class Config:
        from_attributes = True