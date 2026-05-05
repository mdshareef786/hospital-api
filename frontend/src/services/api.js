import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' }
});

// Attach token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Handle 401 globally
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────────
export const login = (data) => api.post('/auth/login',
  new URLSearchParams({ username: data.username, password: data.password }),
  { headers: { 'Content-Type': 'application/x-www-form-urlencoded' }}
);
export const register = (data) => api.post('/auth/register', data);
export const getMe = () => api.get('/auth/me');
export const forgotPassword = (email) => api.post('/auth/forgot-password', { email });
export const resetPassword = (token, new_password) => api.post('/auth/reset-password', { token, new_password });

// ── Doctors ───────────────────────────────────────────────────────────────────
export const getDoctors = (params) => api.get('/doctors', { params });
export const getDoctor = (id) => api.get(`/doctors/${id}`);
export const createDoctor = (data) => api.post('/doctors', data);
export const updateDoctor = (id, data) => api.put(`/doctors/${id}`, data);
export const deleteDoctor = (id) => api.delete(`/doctors/${id}`);
export const toggleDoctorStatus = (id) => api.patch(`/doctors/${id}/toggle-status`);

// ── Patients ──────────────────────────────────────────────────────────────────
export const getPatients = (params) => api.get('/patients', { params });
export const getPatient = (id) => api.get(`/patients/${id}`);
export const createPatient = (data) => api.post('/patients', data);
export const updatePatient = (id, data) => api.put(`/patients/${id}`, data);
export const deletePatient = (id) => api.delete(`/patients/${id}`);

// ── Appointments ──────────────────────────────────────────────────────────────
export const getAppointments = (params) => api.get('/appointments', { params });
export const getAppointment = (id) => api.get(`/appointments/${id}`);
export const createAppointment = (data) => api.post('/appointments', data);
export const updateAppointment = (id, data) => api.put(`/appointments/${id}`, data);
export const cancelAppointment = (id) => api.patch(`/appointments/${id}/cancel`);

// ── Reports ───────────────────────────────────────────────────────────────────
export const getPatientReports = (patientId) => api.get(`/reports/${patientId}`);
export const uploadReport = (patientId, formData) =>
  api.post(`/reports/${patientId}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
export const downloadReport = (reportId) =>
  api.get(`/reports/download/${reportId}`, { responseType: 'blob' });
export const deleteReport = (reportId) => api.delete(`/reports/delete/${reportId}`);

export default api;
