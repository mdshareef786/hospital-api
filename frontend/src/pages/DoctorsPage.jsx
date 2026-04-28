import { useState, useEffect, useCallback } from 'react';
import { getDoctors, createDoctor, updateDoctor, deleteDoctor, toggleDoctorStatus } from '../services/api';
import { useToast } from '../components/Toast';

function DoctorModal({ doctor, onClose, onSave }) {
  const [form, setForm] = useState(doctor || { name: '', specialization: '', email: '', phone: '' });
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (doctor) {
        await updateDoctor(doctor.id, form);
        toast('Doctor updated successfully', 'success');
      } else {
        await createDoctor(form);
        toast('Doctor created successfully', 'success');
      }
      onSave();
    } catch (err) {
      toast(err.response?.data?.detail || 'Error saving doctor', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h2 className="modal-title">{doctor ? 'Edit Doctor' : 'Add Doctor'}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Full Name *</label>
                <input className="form-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required placeholder="Dr. John Smith" />
              </div>
              <div className="form-group">
                <label className="form-label">Specialization *</label>
                <input className="form-input" value={form.specialization} onChange={e => setForm({ ...form, specialization: e.target.value })} required placeholder="Cardiology" />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Email *</label>
              <input className="form-input" type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required placeholder="doctor@hospital.com" />
            </div>
            <div className="form-group">
              <label className="form-label">Phone</label>
              <input className="form-input" value={form.phone || ''} onChange={e => setForm({ ...form, phone: e.target.value })} placeholder="+91 9876543210" />
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Saving...' : doctor ? 'Update Doctor' : 'Add Doctor'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function DoctorsPage() {
  const [data, setData] = useState({ items: [], total: 0, total_pages: 1 });
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [specialization, setSpecialization] = useState('');
  const [modal, setModal] = useState(null); // null | 'create' | doctor object
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const fetchDoctors = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getDoctors({ page, page_size: 10, search: search || undefined, specialization: specialization || undefined });
      setData(res.data);
    } catch {
      toast('Failed to load doctors', 'error');
    } finally {
      setLoading(false);
    }
  }, [page, search, specialization]);

  useEffect(() => { fetchDoctors(); }, [fetchDoctors]);

  const handleDelete = async (id) => {
    if (!confirm('Delete this doctor?')) return;
    try {
      await deleteDoctor(id);
      toast('Doctor deleted', 'success');
      fetchDoctors();
    } catch (err) {
      toast(err.response?.data?.detail || 'Cannot delete doctor', 'error');
    }
  };

  const handleToggle = async (id) => {
    try {
      await toggleDoctorStatus(id);
      toast('Doctor status updated', 'success');
      fetchDoctors();
    } catch {
      toast('Failed to update status', 'error');
    }
  };

  return (
    <div className="page-body">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="section-title">Doctors</h2>
          <p className="text-muted">{data.total} doctor{data.total !== 1 ? 's' : ''} registered</p>
        </div>
        <button className="btn btn-primary" onClick={() => setModal('create')}>
          + Add Doctor
        </button>
      </div>

      <div className="toolbar">
        <input
          className="search-input"
          placeholder="Search by name..."
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1); }}
        />
        <input
          className="search-input"
          placeholder="Filter by specialization..."
          value={specialization}
          onChange={e => { setSpecialization(e.target.value); setPage(1); }}
          style={{ maxWidth: 220 }}
        />
      </div>

      <div className="card">
        {loading ? (
          <div className="empty-state"><div className="icon"></div>Loading...</div>
        ) : data.items.length === 0 ? (
          <div className="empty-state"><div className="icon"></div><div>No doctors found</div></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Name</th><th>Specialization</th><th>Email</th><th>Phone</th><th>Status</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {data.items.map(d => (
                  <tr key={d.id}>
                    <td><strong>{d.name}</strong></td>
                    <td>{d.specialization}</td>
                    <td>{d.email}</td>
                    <td>{d.phone || '—'}</td>
                    <td>
                      <span className={`badge ${d.is_active ? 'badge-success' : 'badge-danger'}`}>
                        {d.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <div className="flex gap-2">
                        <button className="btn btn-sm btn-ghost" onClick={() => setModal(d)}>Edit</button>
                        <button className="btn btn-sm btn-ghost" onClick={() => handleToggle(d.id)}>
                          {d.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button className="btn btn-sm btn-danger" onClick={() => handleDelete(d.id)}>Del</button>
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

      {modal && (
        <DoctorModal
          doctor={modal === 'create' ? null : modal}
          onClose={() => setModal(null)}
          onSave={() => { setModal(null); fetchDoctors(); }}
        />
      )}
    </div>
  );
}
