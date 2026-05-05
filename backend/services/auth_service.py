# ─── Feature 1 & 2: Auth Service with Forgot Password + RBAC ─────────────────
import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models import User, UserRole
from schemas import UserCreate
from services.auth import get_password_hash, verify_password, create_access_token
from config import settings
import logging

logger = logging.getLogger(__name__)


def register_user(db: Session, data: UserCreate) -> User:
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=get_password_hash(data.password),
        role=data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"User registered: {user.username} (role: {user.role})")
    return user


def login_user(db: Session, username: str, password: str) -> dict:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated")

    token = create_access_token(data={"sub": user.username, "role": user.role})
    logger.info(f"User logged in: {user.username}")
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": str(user.created_at)
        }
    }


def forgot_password(db: Session, email: str) -> str:
    """Generate a reset token for the given email."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Don't reveal if email exists — security best practice
        return "If this email is registered, a reset token has been sent."

    reset_token = secrets.token_urlsafe(32)
    user.reset_token = reset_token
    user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
    db.commit()

    logger.info(f"Password reset token generated for: {email}")
    # In production send via email; here we return it directly for testing
    return reset_token


def reset_password(db: Session, token: str, new_password: str) -> bool:
    """Reset password using the token."""
    user = db.query(User).filter(User.reset_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    if user.reset_token_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset token has expired")

    user.hashed_password = get_password_hash(new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    db.commit()

    logger.info(f"Password reset successful for user: {user.username}")
    return True


# ─── Feature 2: RBAC helpers ──────────────────────────────────────────────────

def require_roles(*roles: UserRole):
    """Dependency factory — restrict endpoint to specific roles."""
    from fastapi import Depends
    from services.auth import get_current_user

    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in roles]}"
            )
        return current_user

    return Depends(_check)
