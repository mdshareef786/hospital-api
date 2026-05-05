import logging
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from database import engine, SessionLocal
from models import Base, User
from services.auth import get_password_hash
from utils.exceptions import http_exception_handler, validation_exception_handler, generic_exception_handler
from routers import auth, doctors, patients, appointments, reports, websockets
from config import settings

# ─── FIX: Force UTF-8 for Windows ─────────────────────────────────────────────
sys.stdout.reconfigure(encoding='utf-8')

# ─── Logging (FIXED) ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),                      # console (UTF-8)
        logging.FileHandler("hospital.log", encoding="utf-8")   # file (UTF-8)
    ]
)
logger = logging.getLogger(__name__)

# ─── Rate Limiter ─────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            admin = User(
                username="admin",
                email="admin@hospital.com",
                hashed_password=get_password_hash("admin123"),
                role="admin"
            )
            db.add(admin)
            db.commit()
            logger.info("Default admin created: admin / admin123")
    finally:
        db.close()
    logger.info("Hospital Management System started ✅")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Hospital Management System",
    version="2.0.0",
    lifespan=lifespan
)

# ─── Rate Limiter ─────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── Global Exception Handlers ────────────────────────────────────────────────
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Request Logging (SAFE) ───────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    try:
        logger.info(f"→ {request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"← {request.method} {request.url.path} [{response.status_code}]")
        return response
    except Exception as e:
        logger.error(f"Logging failed: {e}")
        raise

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(doctors.router)
app.include_router(patients.router)
app.include_router(appointments.router)
app.include_router(reports.router)
app.include_router(websockets.router)

@app.get("/", tags=["Health"])
def root():
    return {"success": True, "message": "Hospital Management System API v2.0", "docs": "/docs"}

@app.get("/health", tags=["Health"])
def health():
    return {"success": True, "message": "healthy", "version": "2.0.0"}
