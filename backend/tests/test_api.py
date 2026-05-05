import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import get_db, Base
from models import User
from services.auth import get_password_hash

# Test DB
TEST_DB_URL = "sqlite:///./test_hospital.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
    if not db.query(User).filter(User.username == "testadmin").first():
        admin = User(
            username="testadmin",
            email="testadmin@hospital.com",
            hashed_password=get_password_hash("test123"),
            role="admin"
        )
        db.add(admin)
        db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    # Use form data instead of JSON
    response = client.post("/auth/login", data={
        "username": "testadmin",
        "password": "test123"
    })
    data = response.json()
    # Handle both { access_token } and { data: { access_token } }
    payload = data.get("data") or data
    token = payload.get("access_token")
    return {"Authorization": f"Bearer {token}"}


# ─── Auth Tests ───────────────────────────────────────────────────────────────

def test_login_success(client):
    response = client.post("/auth/login", data={
        "username": "testadmin",
        "password": "test123"
    })
    assert response.status_code == 200


def test_login_wrong_password(client):
    response = client.post("/auth/login", data={
        "username": "testadmin",
        "password": "wrong"
    })
    assert response.status_code == 401


def test_protected_route_without_token(client):
    response = client.get("/doctors")
    assert response.status_code == 401


# ─── Doctor Tests ─────────────────────────────────────────────────────────────

def test_create_doctor(client, auth_headers):
    response = client.post("/doctors", json={
        "name": "Dr. Smith",
        "specialization": "Cardiology",
        "email": "smith@hospital.com"
    }, headers=auth_headers)
    assert response.status_code == 201


def test_create_doctor_invalid_email(client, auth_headers):
    response = client.post("/doctors", json={
        "name": "Dr. Bad",
        "specialization": "Cardiology",
        "email": "not-an-email"
    }, headers=auth_headers)
    assert response.status_code == 422


def test_list_doctors(client, auth_headers):
    client.post("/doctors", json={
        "name": "Dr. Jones",
        "specialization": "Neurology",
        "email": "jones@hospital.com"
    }, headers=auth_headers)
    response = client.get("/doctors", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] >= 1


def test_get_doctor_not_found(client, auth_headers):
    response = client.get("/doctors/9999", headers=auth_headers)
    assert response.status_code == 404


def test_update_doctor(client, auth_headers):
    create = client.post("/doctors", json={
        "name": "Dr. Update",
        "specialization": "General",
        "email": "update@hospital.com"
    }, headers=auth_headers)
    doctor_id = create.json()["data"]["id"]
    response = client.put(f"/doctors/{doctor_id}", json={
        "specialization": "Oncology"
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["specialization"] == "Oncology"


def test_toggle_doctor_status(client, auth_headers):
    create = client.post("/doctors", json={
        "name": "Dr. Toggle",
        "specialization": "General",
        "email": "toggle@hospital.com"
    }, headers=auth_headers)
    doctor_id = create.json()["data"]["id"]
    response = client.patch(f"/doctors/{doctor_id}/toggle-status",
                           headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["is_active"] is False


# ─── Patient Tests ────────────────────────────────────────────────────────────

def test_create_patient(client, auth_headers):
    response = client.post("/patients", json={
        "name": "John Doe",
        "age": 35,
        "phone": "9876543210"
    }, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["data"]["name"] == "John Doe"


def test_create_patient_invalid_age(client, auth_headers):
    response = client.post("/patients", json={
        "name": "Bad Patient",
        "age": -1,
        "phone": "1234567890"
    }, headers=auth_headers)
    assert response.status_code == 422


def test_search_patient(client, auth_headers):
    client.post("/patients", json={
        "name": "Alice Wonder",
        "age": 28,
        "phone": "1111111111"
    }, headers=auth_headers)
    response = client.get("/patients?search=Alice", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["total"] >= 1


# ─── Appointment Tests ────────────────────────────────────────────────────────

def test_create_appointment(client, auth_headers):
    doc = client.post("/doctors", json={
        "name": "Dr. Appt",
        "specialization": "General",
        "email": "appt.doc@hospital.com"
    }, headers=auth_headers).json()["data"]

    pat = client.post("/patients", json={
        "name": "Appt Patient",
        "age": 40,
        "phone": "2222222222"
    }, headers=auth_headers).json()["data"]

    response = client.post("/appointments", json={
        "doctor_id": doc["id"],
        "patient_id": pat["id"],
        "appointment_date": "2099-12-01T10:00:00"
    }, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["data"]["status"] == "Pending"


def test_cancel_appointment(client, auth_headers):
    doc = client.post("/doctors", json={
        "name": "Dr. Cancel",
        "specialization": "General",
        "email": "cancel.doc@hospital.com"
    }, headers=auth_headers).json()["data"]

    pat = client.post("/patients", json={
        "name": "Cancel Patient",
        "age": 30,
        "phone": "3333333333"
    }, headers=auth_headers).json()["data"]

    appt = client.post("/appointments", json={
        "doctor_id": doc["id"],
        "patient_id": pat["id"],
        "appointment_date": "2099-11-01T09:00:00"
    }, headers=auth_headers).json()["data"]

    response = client.patch(f"/appointments/{appt['id']}/cancel",
                           headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "Cancelled"
