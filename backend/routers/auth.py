from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserRole
from schemas import UserCreate, UserResponse, ForgotPasswordRequest, ResetPasswordRequest
from services.auth import get_current_user
from services.auth_service import register_user, login_user, forgot_password, reset_password
from utils.response import success_response

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    user = register_user(db, user_data)
    return success_response("User registered successfully", UserResponse.model_validate(user))


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return login_user(db, form_data.username, form_data.password)


@router.post("/forgot-password")
def forgot_password_endpoint(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request a password reset token. In production this would be emailed."""
    token = forgot_password(db, data.email)
    return success_response(
        "Reset token generated (in production this would be emailed)",
        {"reset_token": token}
    )


@router.post("/reset-password")
def reset_password_endpoint(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    reset_password(db, data.token, data.new_password)
    return success_response("Password reset successfully")


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return success_response("Current user", UserResponse.model_validate(current_user))
