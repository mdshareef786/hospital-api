# 🏥 Hospital Management System

A full-stack hospital management application built with **FastAPI** (Python) + **React** (Vite), featuring JWT authentication, real-time WebSocket notifications, file uploads, and more.

---

## 📁 Project Structure

```
hospital-management/
├── backend/
│   ├── main.py                      # FastAPI app entry point
│   ├── database.py                  # SQLAlchemy DB setup
│   ├── config.py                    # Environment settings
│   ├── requirements.txt
│   ├── .env                         # Environment variables
│   ├── models/
│   │   └── __init__.py              # SQLAlchemy ORM models
│   ├── schemas/
│   │   └── __init__.py              # Pydantic schemas
│   ├── routers/
│   │   ├── auth.py                  # Login / Register / Forgot Password
│   │   ├── doctors.py               # Doctor CRUD
│   │   ├── patients.py              # Patient CRUD
│   │   ├── appointments.py          # Appointment management
│   │   ├── reports.py               # File upload/download
│   │   └── websockets.py            # WebSocket endpoints
│   ├── services/
│   │   ├── auth.py                  # JWT utilities
│   │   ├── auth_service.py          # Auth business logic + RBAC
│   │   ├── doctor_service.py        # Doctor business logic + Cache
│   │   ├── patient_service.py       # Patient business logic
│   │   ├── appointment_service.py   # Appointment + double booking prevention
│   │   └── websocket_manager.py     # WS connection manager
│   ├── utils/
│   │   ├── response.py              # Standard API response format
│   │   ├── cache.py                 # In-memory cache
│   │   └── exceptions.py            # Global exception handlers
│   └── tests/
│       └── test_api.py              # Pytest test suite
│
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── package.json
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── index.css
        ├── context/
        │   └── AuthContext.jsx
        ├── services/
        │   ├── api.js
        │   └── useWebSocket.js
        ├── components/
        │   ├── Sidebar.jsx
        │   └── Toast.jsx
        └── pages/
            ├── LoginPage.jsx
            ├── DashboardPage.jsx
            ├── DoctorsPage.jsx
            ├── PatientsPage.jsx
            └── AppointmentsPage.jsx
```
---

## ⚙️ Backend Setup

### Prerequisites
- Python 3.11 (recommended)
- pip
- Node.js 18+

### Installation

```bash
cd backend
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

API starts at **http://localhost:8000**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Default credentials:** Username: `admin` | Password: `admin123`

---

## 🖥️ Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:3000**

---

## 🔌 API Endpoints

### 🔐 Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login & get JWT token |
| GET | `/auth/me` | Get current user |
| POST | `/auth/forgot-password` | Request password reset token |
| POST | `/auth/reset-password` | Reset password using token |

### 👨‍⚕️ Doctors
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/doctors` | Create doctor (Admin only) |
| GET | `/doctors` | List doctors (pagination, search, sort, filter) |
| GET | `/doctors/{id}` | Get doctor by ID |
| PUT | `/doctors/{id}` | Update doctor (Admin only) |
| DELETE | `/doctors/{id}` | Delete doctor (Admin only) |
| PATCH | `/doctors/{id}/toggle-status` | Activate/Deactivate (Admin only) |

### 🏥 Patients
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/patients` | Create patient (Admin/Doctor) |
| GET | `/patients` | List patients (pagination, search, sort) |
| GET | `/patients/{id}` | Get patient by ID |
| PUT | `/patients/{id}` | Update patient (Admin/Doctor) |
| DELETE | `/patients/{id}` | Delete patient (Admin only) |

### 📅 Appointments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/appointments` | Book appointment |
| GET | `/appointments` | List (filter by doctor/patient/status/date) |
| GET | `/appointments/{id}` | Get appointment |
| PUT | `/appointments/{id}` | Update appointment (Admin/Doctor) |
| PATCH | `/appointments/{id}/cancel` | Cancel appointment |

### 📁 Patient Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/reports/{patient_id}/upload` | Upload file |
| GET | `/reports/{patient_id}` | List patient reports |
| GET | `/reports/download/{report_id}` | Download file |
| DELETE | `/reports/delete/{report_id}` | Delete report |

### 🔔 WebSockets
| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8000/ws/dashboard` | Admin dashboard live updates |
| `ws://localhost:8000/ws/doctor/{id}` | Doctor-specific notifications |

---

## ✅ Features

### v1.0
- JWT Authentication — secure token-based login, protected routes
- Doctor Management — Full CRUD, activate/deactivate, filter by specialization
- Patient Management — Full CRUD, search by name/phone
- Appointments — Book, update status, cancel
- Real-time WebSockets — Live appointment notifications
- File Uploads — Upload patient reports (PDF, images, docs), download, delete
- Pagination — All listing APIs support page & page_size
- Rate Limiting — 200 requests/minute per IP
- Logging — All requests logged to console + hospital.log
- Background Tasks — WebSocket notifications via FastAPI BackgroundTasks
- Pytest Tests — 14 tests covering all major APIs

### v2.0 (Latest)
- Forgot Password — Token-based password reset flow
- Role-Based Access Control — Admin / Doctor / Patient roles
- New Appointment Statuses — Pending / Approved / Rejected / Completed / Cancelled
- Double Booking Prevention — 30-minute slot validation per doctor
- Service Layer Architecture — All business logic moved to services folder
- Sorting — All listing APIs support sort_by and sort_order=asc/desc
- Standard API Response Format — { success, message, data, errors } on every API
- Global Exception Handler — Clean consistent error responses
- In-Memory Caching — Doctor list cached for 60 seconds, auto-invalidated

---

## 🧪 Running Tests

```bash
cd backend
pytest tests/test_api.py -v
```

Tests cover: auth login/register, doctor CRUD, patient CRUD, appointment booking and cancellation.

---

## 🌍 Environment Variables (.env)

```env
SECRET_KEY=your-super-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DATABASE_URL=sqlite:///./hospital.db
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=10
```

---

## 🐳 Docker (Optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📸 API Testing

Use **Swagger UI** at http://localhost:8000/docs
Click **Authorize** → enter username: `admin` password: `admin123` → test all endpoints directly in browser.

