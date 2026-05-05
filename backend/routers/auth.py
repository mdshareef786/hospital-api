from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import get_db
from schemas import UserCreate, UserResponse, ForgotPasswordRequest, ResetPasswordRequest
from services.auth import get_current_user
from services.auth_service import register_user, login_user, forgot_password, reset_password
from utils.response import success_response

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    user = register_user(db, user_data)
    return success_response("User registered", UserResponse.model_validate(user))


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return login_user(db, form_data.username, form_data.password)


@router.post("/forgot-password")
def forgot_password_endpoint(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    token = forgot_password(db, data.email)
    return success_response("Reset token generated", {"reset_token": token})


@router.post("/reset-password")
def reset_password_endpoint(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    reset_password(db, data.token, data.new_password)
    return success_response("Password reset successful")


@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    return success_response("Current user", UserResponse.model_validate(current_user))