import { useState, useEffect, useCallback } from 'react';
import { getAppointments, createAppointment, updateAppointment, cancelAppointment, getDoctors, getPatients } from '../services/api';
import { useToast } from '../components/Toast';

function AppointmentModal({ onClose, onSave }) {
  const [form, setForm] = useState({ doctor_id: '', patient_id: '', appointment_date: '', notes: '' });
  const [doctors, setDoctors] = useState([]);
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  useEffect(() => {
    getDoctors({ page: 1, page_size: 100, is_active: true }).then(r => setDoctors(r.data.items || []));
    getPatients({ page: 1, page_size: 100, is_active: true }).then(r => setPatients(r.data.items || []));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createAppointment({
        doctor_id: Number(form.doctor_id),
        patient_id: Number(form.patient_id),
        appointment_date: new Date(form.appointment_date).toISOString(),
        notes: form.notes || undefined,
      });
      toast('Appointment booked successfully!', 'success');
      onSave();
    } catch (err) {
      toast(err.response?.data?.detail || 'Failed to book appointment', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h2 className="modal-title">📅 Book Appointment</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-group">
              <label className="form-label">Select Doctor *</label>
              <select className="form-select" value={form.doctor_id} onChange={e => setForm({ ...form, doctor_id: e.target.value })} required>
                <option value="">— Choose Doctor —</option>
                {doctors.map(d => (
                  <option key={d.id} value={d.id}>{d.name} ({d.specialization})</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Select Patient *</label>
              <select className="form-select" value={form.patient_id} onChange={e => setForm({ ...form, patient_id: e.target.value })} required>
                <option value="">— Choose Patient —</option>
                {patients.map(p => (
                  <option key={p.id} value={p.id}>{p.name} (Age: {p.age})</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Appointment Date & Time *</label>
              <input className="form-input" type="datetime-local" value={form.appointment_date} onChange={e => setForm({ ...form, appointment_date: e.target.value })} required min={new Date().toISOString().slice(0, 16)} />
            </div>
            <div className="form-group">
              <label className="form-label">Notes</label>
              <textarea className="form-textarea" value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} placeholder="Additional notes or symptoms..." />
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? 'Booking...' : 'Book Appointment'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}

function StatusModal({ appointment, onClose, onSave }) {
  const [status, setStatus] = useState(appointment.status);
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const handleUpdate = async () => {
    setLoading(true);
    try {
      await updateAppointment(appointment.id, { status });
      toast('Status updated', 'success');
      onSave();
    } catch (err) {
      toast(err.response?.data?.detail || 'Failed to update', 'error');
    } finally { setLoading(false); }
  };

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h2 className="modal-title">Update Appointment #{appointment.id}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          <div className="form-group">
            <label className="form-label">Status</label>
            <select className="form-select" value={status} onChange={e => setStatus(e.target.value)}>
              <option value="Scheduled">Scheduled</option>
              <option value="Completed">Completed</option>
              <option value="Cancelled">Cancelled</option>
            </select>
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={handleUpdate} disabled={loading}>{loading ? 'Saving...' : 'Update Status'}</button>
        </div>
      </div>
    </div>
  );
}

const STATUS_BADGE = { Scheduled: 'badge-info', Completed: 'badge-success', Cancelled: 'badge-danger' };

export default function AppointmentsPage() {
  const [data, setData] = useState({ items: [], total: 0, total_pages: 1 });
  const [page, setPage] = useState(1);
  const [filterStatus, setFilterStatus] = useState('');
  const [modal, setModal] = useState(null); // 'create' | appointment for status
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const fetchAppointments = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getAppointments({ page, page_size: 10, status: filterStatus || undefined });
      setData(res.data);
    } catch { toast('Failed to load appointments', 'error'); }
    finally { setLoading(false); }
  }, [page, filterStatus]);

  useEffect(() => { fetchAppointments(); }, [fetchAppointments]);

  const handleCancel = async (id) => {
    if (!confirm('Cancel this appointment?')) return;
    try {
      await cancelAppointment(id);
      toast('Appointment cancelled', 'success');
      fetchAppointments();
    } catch (err) {
      toast(err.response?.data?.detail || 'Failed to cancel', 'error');
    }
  };

  return (
    <div className="page-body">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="section-title">Appointments</h2>
          <p className="text-muted">{data.total} total appointment{data.total !== 1 ? 's' : ''}</p>
        </div>
        <button className="btn btn-primary" onClick={() => setModal('create')}>+ Book Appointment</button>
      </div>

      <div className="toolbar">
        <select className="form-select" style={{ maxWidth: 200 }} value={filterStatus} onChange={e => { setFilterStatus(e.target.value); setPage(1); }}>
          <option value="">All Statuses</option>
          <option value="Scheduled">Scheduled</option>
          <option value="Completed">Completed</option>
          <option value="Cancelled">Cancelled</option>
        </select>
      </div>

      <div className="card">
        {loading ? (
          <div className="empty-state"><div className="icon">⏳</div>Loading...</div>
        ) : data.items.length === 0 ? (
          <div className="empty-state"><div className="icon">📅</div><div>No appointments found</div></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>ID</th><th>Doctor</th><th>Patient</th><th>Date & Time</th><th>Status</th><th>Notes</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {data.items.map(a => (
                  <tr key={a.id}>
                    <td>#{a.id}</td>
                    <td><strong>{a.doctor?.name || `#${a.doctor_id}`}</strong><br /><span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{a.doctor?.specialization}</span></td>
                    <td>{a.patient?.name || `#${a.patient_id}`}<br /><span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Age: {a.patient?.age}</span></td>
                    <td>{new Date(a.appointment_date).toLocaleString()}</td>
                    <td><span className={`badge ${STATUS_BADGE[a.status] || 'badge-gray'}`}>{a.status}</span></td>
                    <td style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{a.notes || '—'}</td>
                    <td>
                      <div className="flex gap-2">
                        {a.status !== 'Cancelled' && (
                          <>
                            <button className="btn btn-sm btn-ghost" onClick={() => setModal(a)}>Update</button>
                            <button className="btn btn-sm btn-danger" onClick={() => handleCancel(a.id)}>Cancel</button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {data.total_pages > 1 && (
          <div className="pagination">
            <button className="page-btn" disabled={page === 1} onClick={() => setPage(p => p - 1)}>‹ Prev</button>
            {Array.from({ length: data.total_pages }, (_, i) => i + 1).map(p => (
              <button key={p} className={`page-btn ${p === page ? 'active' : ''}`} onClick={() => setPage(p)}>{p}</button>
            ))}
            <button className="page-btn" disabled={page === data.total_pages} onClick={() => setPage(p => p + 1)}>Next ›</button>
          </div>
        )}
      </div>

      {modal === 'create' && (
        <AppointmentModal onClose={() => setModal(null)} onSave={() => { setModal(null); fetchAppointments(); }} />
      )}
      {modal && modal !== 'create' && (
        <StatusModal appointment={modal} onClose={() => setModal(null)} onSave={() => { setModal(null); fetchAppointments(); }} />
      )}
    </div>
  );
}
