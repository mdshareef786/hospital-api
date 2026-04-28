import { useState, useEffect, useCallback } from 'react';
import { getPatients, createPatient, updatePatient, deletePatient, getPatientReports, uploadReport, downloadReport, deleteReport } from '../services/api';
import { useToast } from '../components/Toast';

function PatientModal({ patient, onClose, onSave }) {
  const [form, setForm] = useState(patient || { name: '', age: '', phone: '', email: '', address: '' });
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = { ...form, age: Number(form.age) };
      if (patient) {
        await updatePatient(patient.id, payload);
        toast('Patient updated', 'success');
      } else {
        await createPatient(payload);
        toast('Patient created', 'success');
      }
      onSave();
    } catch (err) {
      toast(err.response?.data?.detail || 'Error saving patient', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h2 className="modal-title">{patient ? 'Edit Patient' : 'Add Patient'}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Full Name *</label>
                <input className="form-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required placeholder="John Doe" />
              </div>
              <div className="form-group">
                <label className="form-label">Age *</label>
                <input className="form-input" type="number" min={1} max={149} value={form.age} onChange={e => setForm({ ...form, age: e.target.value })} required placeholder="35" />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Phone *</label>
                <input className="form-input" value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} required placeholder="9876543210" />
              </div>
              <div className="form-group">
                <label className="form-label">Email</label>
                <input className="form-input" type="email" value={form.email || ''} onChange={e => setForm({ ...form, email: e.target.value })} placeholder="patient@email.com" />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Address</label>
              <textarea className="form-textarea" value={form.address || ''} onChange={e => setForm({ ...form, address: e.target.value })} placeholder="123 Main St, City" />
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? 'Saving...' : patient ? 'Update' : 'Add Patient'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ReportsModal({ patient, onClose }) {
  const [reports, setReports] = useState([]);
  const [file, setFile] = useState(null);
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const toast = useToast();

  const fetchReports = async () => {
    try {
      const res = await getPatientReports(patient.id);
      setReports(res.data);
    } catch { toast('Failed to load reports', 'error'); }
  };

  useEffect(() => { fetchReports(); }, []);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      if (description) fd.append('description', description);
      await uploadReport(patient.id, fd);
      toast('Report uploaded', 'success');
      setFile(null);
      setDescription('');
      fetchReports();
    } catch (err) {
      toast(err.response?.data?.detail || 'Upload failed', 'error');
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (report) => {
    try {
      const res = await downloadReport(report.id);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url; a.download = report.original_filename; a.click();
    } catch { toast('Download failed', 'error'); }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this report?')) return;
    try {
      await deleteReport(id);
      toast('Report deleted', 'success');
      fetchReports();
    } catch { toast('Delete failed', 'error'); }
  };

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal" style={{ maxWidth: 580 }}>
        <div className="modal-header">
          <h2 className="modal-title">📁 Reports — {patient.name}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          <div style={{ background: '#f8f7f4', borderRadius: 8, padding: 16, marginBottom: 20 }}>
            <div className="form-group" style={{ marginBottom: 10 }}>
              <label className="form-label">Upload New Report</label>
              <input type="file" className="form-input" onChange={e => setFile(e.target.files[0])} accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.txt" />
            </div>
            <div className="form-group" style={{ marginBottom: 10 }}>
              <input className="form-input" placeholder="Description (optional)" value={description} onChange={e => setDescription(e.target.value)} />
            </div>
            <button className="btn btn-primary btn-sm" onClick={handleUpload} disabled={!file || uploading}>
              {uploading ? 'Uploading...' : '⬆ Upload'}
            </button>
          </div>

          {reports.length === 0 ? (
            <div className="empty-state"><div className="icon">📄</div><div>No reports uploaded yet</div></div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {reports.map(r => (
                <div key={r.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px', background: '#fff', border: '1px solid var(--border)', borderRadius: 8 }}>
                  <span style={{ fontSize: '1.4rem' }}>📄</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 500, fontSize: '0.875rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.original_filename}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {r.description} · {r.file_size ? `${(r.file_size / 1024).toFixed(1)} KB` : ''} · {new Date(r.uploaded_at).toLocaleDateString()}
                    </div>
                  </div>
                  <button className="btn btn-sm btn-ghost" onClick={() => handleDownload(r)}>⬇</button>
                  <button className="btn btn-sm btn-danger" onClick={() => handleDelete(r.id)}>🗑</button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function PatientsPage() {
  const [data, setData] = useState({ items: [], total: 0, total_pages: 1 });
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState(null);
  const [reportsModal, setReportsModal] = useState(null);
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const fetchPatients = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getPatients({ page, page_size: 10, search: search || undefined });
      setData(res.data);
    } catch {
      toast('Failed to load patients', 'error');
    } finally { setLoading(false); }
  }, [page, search]);

  useEffect(() => { fetchPatients(); }, [fetchPatients]);

  const handleDelete = async (id) => {
    if (!confirm('Delete this patient?')) return;
    try {
      await deletePatient(id);
      toast('Patient deleted', 'success');
      fetchPatients();
    } catch (err) {
      toast(err.response?.data?.detail || 'Cannot delete patient', 'error');
    }
  };

  return (
    <div className="page-body">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="section-title">Patients</h2>
          <p className="text-muted">{data.total} patient{data.total !== 1 ? 's' : ''} registered</p>
        </div>
        <button className="btn btn-primary" onClick={() => setModal('create')}>+ Add Patient</button>
      </div>

      <div className="toolbar">
        <input className="search-input" placeholder="Search by name or phone..." value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
      </div>

      <div className="card">
        {loading ? (
          <div className="empty-state"><div className="icon">⏳</div>Loading...</div>
        ) : data.items.length === 0 ? (
          <div className="empty-state"><div className="icon">🏥</div><div>No patients found</div></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Name</th><th>Age</th><th>Phone</th><th>Email</th><th>Status</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {data.items.map(p => (
                  <tr key={p.id}>
                    <td><strong>{p.name}</strong></td>
                    <td>{p.age} yrs</td>
                    <td>{p.phone}</td>
                    <td>{p.email || '—'}</td>
                    <td><span className={`badge ${p.is_active ? 'badge-success' : 'badge-danger'}`}>{p.is_active ? 'Active' : 'Inactive'}</span></td>
                    <td>
                      <div className="flex gap-2">
                        <button className="btn btn-sm btn-ghost" onClick={() => setModal(p)}>Edit</button>
                        <button className="btn btn-sm btn-ghost" onClick={() => setReportsModal(p)}>📁 Reports</button>
                        <button className="btn btn-sm btn-danger" onClick={() => handleDelete(p.id)}>Del</button>
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
        <PatientModal patient={modal === 'create' ? null : modal} onClose={() => setModal(null)} onSave={() => { setModal(null); fetchPatients(); }} />
      )}
      {reportsModal && (
        <ReportsModal patient={reportsModal} onClose={() => setReportsModal(null)} />
      )}
    </div>
  );
}
