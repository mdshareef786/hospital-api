# 🏥 Hospital Management System

A full-stack hospital management application built with **FastAPI** (Python) + **React** (Vite), featuring JWT authentication, real-time WebSocket notifications, file uploads, and more.

---

## 📁 Project Structure

```
hospital-management/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── database.py             # SQLAlchemy DB setup
│   ├── config.py               # Environment settings
│   ├── requirements.txt
│   ├── .env                    # Environment variables
│   ├── models/
│   │   └── __init__.py         # SQLAlchemy ORM models
│   ├── schemas/
│   │   └── __init__.py         # Pydantic schemas
│   ├── routers/
│   │   ├── auth.py             # Login / Register
│   │   ├── doctors.py          # Doctor CRUD
│   │   ├── patients.py         # Patient CRUD
│   │   ├── appointments.py     # Appointment management
│   │   ├── reports.py          # File upload/download
│   │   └── websockets.py       # WebSocket endpoints
│   ├── services/
│   │   ├── auth.py             # JWT utilities
│   │   └── websocket_manager.py # WS connection manager
│   └── tests/
│       └── test_api.py         # Pytest test suite
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
- Python 3.9+ (tested on 3.14.3)
- pip

### Installation

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Mac/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --port 8000
```

The API will start at **http://localhost:8000**

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Default admin credentials created on first run:**
- Username: `admin`
- Password: `admin123`

---

## 🖥️ Frontend Setup

### Prerequisites
- Node.js 18+
- npm

### Installation

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
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

### 👨‍⚕️ Doctors
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/doctors` | Create doctor |
| GET | `/doctors` | List doctors (pagination, search, filter) |
| GET | `/doctors/{id}` | Get doctor by ID |
| PUT | `/doctors/{id}` | Update doctor |
| DELETE | `/doctors/{id}` | Delete doctor |
| PATCH | `/doctors/{id}/toggle-status` | Activate/Deactivate |

### 🏥 Patients
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/patients` | Create patient |
| GET | `/patients` | List patients (pagination, search) |
| GET | `/patients/{id}` | Get patient by ID |
| PUT | `/patients/{id}` | Update patient |
| DELETE | `/patients/{id}` | Delete patient |

### 📅 Appointments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/appointments` | Book appointment |
| GET | `/appointments` | List appointments (filter by doctor/patient/status) |
| GET | `/appointments/{id}` | Get appointment |
| PUT | `/appointments/{id}` | Update appointment |
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

- **JWT Authentication** — secure token-based login, protected routes
- **Role-based access** — Admin / Doctor roles
- **Doctor Management** — Full CRUD, activate/deactivate, filter by specialization
- **Patient Management** — Full CRUD, search by name/phone
- **Appointments** — Book, update status (Scheduled/Completed/Cancelled), cancel
- **Real-time WebSockets** — Doctor gets notified when appointment is booked; admin dashboard gets all updates
- **File Uploads** — Upload patient reports (PDF, images, docs), download, delete
- **Pagination** — All listing APIs support page & page_size
- **Search & Filtering** — Doctors by name/specialization, patients by name/phone, appointments by status
- **Rate Limiting** — 200 requests/minute per IP (slowapi)
- **Logging** — All requests and errors logged to console + `hospital.log`
- **Background Tasks** — WebSocket notifications sent as FastAPI background tasks
- **Pydantic Validation** — Email format, age > 0, required fields, etc.
- **SQLite + SQLAlchemy ORM** — Easy to swap to MySQL/PostgreSQL

---

## 🧪 Running Tests

```bash
cd backend
pytest tests/test_api.py -v
```

Tests cover: auth login/register, doctor CRUD, patient CRUD, appointment booking and cancellation.

---

## 🌍 Environment Variables (`.env`)

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

### Backend Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
version: "3.9"
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
```

---

## 📸 API Testing

Use the interactive **Swagger UI** at http://localhost:8000/docs to test all endpoints directly in the browser. Click **Authorize** and enter your Bearer token after logging in.
