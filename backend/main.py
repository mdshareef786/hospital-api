import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database import engine, SessionLocal
from models import Base, User, UserRole
from services.auth import get_password_hash

from utils.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)
from utils.response import success_response

from routers import auth, doctors, patients, appointments, reports, websockets
from config import settings


# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("hospital.log", mode="a")
    ]
)
logger = logging.getLogger(__name__)


# ─── Rate Limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Ensure upload dir exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Create default admin
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            admin = User(
                username="admin",
                email="admin@hospital.com",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.admin   # 🔥 FIXED
            )
            db.add(admin)
            db.commit()
            logger.info("Default admin created (admin/admin123)")
    finally:
        db.close()

    logger.info("Application started")
    yield
    logger.info("Application shutting down...")


app = FastAPI(
    title="Hospital Management System",
    version="2.0.0",
    lifespan=lifespan
)


# ─── Rate Limiter ──────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ─── Exception Handlers ───────────────────────────────────────────────────────
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# ─── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request Logging ───────────────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"→ {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"← {request.method} {request.url.path} [{response.status_code}]")
    return response


# ─── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(doctors.router)
app.include_router(patients.router)
app.include_router(appointments.router)
app.include_router(reports.router)
app.include_router(websockets.router)


# ─── Health Endpoints ──────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return success_response("Hospital Management API", {"docs": "/docs"})


@app.get("/health", tags=["Health"])
def health():
    return success_response("Service is healthy", {"version": "2.0.0"})