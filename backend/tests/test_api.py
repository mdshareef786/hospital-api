import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import get_db, Base
from models import User, UserRole
from services.auth import get_password_hash

# DB setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    admin = User(
        username="admin",
        email="admin@test.com",
        hashed_password=get_password_hash("admin123"),
        role=UserRole.admin
    )

    patient_user = User(
        username="patient",
        email="patient@test.com",
        hashed_password=get_password_hash("patient123"),
        role=UserRole.patient
    )

    db.add_all([admin, patient_user])
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def get_token(client, username, password):
    response = client.post(
        "/auth/login",
        data={"username": username, "password": password}
    )
    return response.json()["data"]["access_token"]


@pytest.fixture
def admin_headers(client):
    token = get_token(client, "admin", "admin123")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def patient_headers(client):
    token = get_token(client, "patient", "patient123")
    return {"Authorization": f"Bearer {token}"}


# ─── AUTH ─────────────────────────────────────

def test_login(client):
    res = client.post("/auth/login", data={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    assert "access_token" in res.json()["data"]


# ─── DOCTOR ───────────────────────────────────

def test_create_doctor(client, admin_headers):
    res = client.post("/doctors", json={
        "name": "Dr A",
        "specialization": "Cardiology",
        "email": "a@test.com",
        "user_id": 1
    }, headers=admin_headers)

    assert res.status_code == 200


def test_list_doctors(client, admin_headers):
    res = client.get("/doctors", headers=admin_headers)
    assert res.status_code == 200
    assert "data" in res.json()


# ─── PATIENT ──────────────────────────────────

def test_create_patient(client, patient_headers):
    res = client.post("/patients", json={
        "name": "John",
        "age": 30,
        "phone": "9999999999",
        "user_id": 2
    }, headers=patient_headers)

    assert res.status_code == 200


# ─── APPOINTMENT ──────────────────────────────

def test_create_appointment(client, admin_headers, patient_headers):

    doc = client.post("/doctors", json={
        "name": "Dr B",
        "specialization": "General",
        "email": "b@test.com",
        "user_id": 1
    }, headers=admin_headers).json()["data"]

    pat = client.post("/patients", json={
        "name": "Patient A",
        "age": 25,
        "phone": "8888888888",
        "user_id": 2
    }, headers=patient_headers).json()["data"]

    res = client.post("/appointments", json={
        "doctor_id": doc["id"],
        "patient_id": pat["id"],
        "appointment_date": "2099-01-01T10:00:00"
    }, headers=patient_headers)

    assert res.status_code == 200
    assert res.json()["data"]["status"] == "pending"


def test_cancel_appointment(client, admin_headers, patient_headers):

    doc = client.post("/doctors", json={
        "name": "Dr C",
        "specialization": "General",
        "email": "c@test.com",
        "user_id": 1
    }, headers=admin_headers).json()["data"]

    pat = client.post("/patients", json={
        "name": "Patient B",
        "age": 28,
        "phone": "7777777777",
        "user_id": 2
    }, headers=patient_headers).json()["data"]

    appt = client.post("/appointments", json={
        "doctor_id": doc["id"],
        "patient_id": pat["id"],
        "appointment_date": "2099-01-01T11:00:00"
    }, headers=patient_headers).json()["data"]

    res = client.patch(f"/appointments/{appt['id']}/cancel", headers=patient_headers)

    assert res.status_code == 200