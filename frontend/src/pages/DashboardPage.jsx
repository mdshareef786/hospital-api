import { useState, useEffect } from 'react';
import { getDoctors, getPatients, getAppointments } from '../services/api';
import { useWebSocket } from '../services/useWebSocket';

export default function DashboardPage() {
  const [stats, setStats] = useState({ doctors: 0, patients: 0, appointments: 0, scheduled: 0 });
  const [recentAppointments, setRecentAppointments] = useState([]);
  const [showNotifs, setShowNotifs] = useState(false);
  const { messages, connected, clearMessages } = useWebSocket('ws://localhost:8000/ws/dashboard');

  useEffect(() => {
    Promise.all([
      getDoctors({ page: 1, page_size: 1 }),
      getPatients({ page: 1, page_size: 1 }),
      getAppointments({ page: 1, page_size: 5 }),
      getAppointments({ page: 1, page_size: 1, status: 'Scheduled' }),
    ]).then(([docs, pats, appts, scheduled]) => {
      setStats({
        doctors: docs.data.total,
        patients: pats.data.total,
        appointments: appts.data.total,
        scheduled: scheduled.data.total,
      });
      setRecentAppointments(appts.data.items || []);
    }).catch(() => {});
  }, []);

  const statusBadge = (s) => {
    const map = { Scheduled: 'badge-info', Completed: 'badge-success', Cancelled: 'badge-danger' };
    return <span className={`badge ${map[s] || 'badge-gray'}`}>{s}</span>;
  };

  return (
    <div className="page-body">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="section-title">Dashboard</h2>
          <p className="text-muted">Welcome back! Here's your hospital overview.</p>
        </div>
        <div style={{ position: 'relative' }}>
          <button className="notif-btn" onClick={() => setShowNotifs(!showNotifs)}>
            🔔
            {messages.length > 0 && <span className="notif-dot" />}
          </button>
          {showNotifs && (
            <div style={{
              position: 'absolute', right: 0, top: 44, width: 320, background: '#fff',
              border: '1px solid var(--border)', borderRadius: 12, boxShadow: 'var(--shadow-hover)', zIndex: 100
            }}>
              <div className="flex justify-between items-center" style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)' }}>
                <strong style={{ fontSize: '0.9rem' }}>
                  Live Notifications
                  <span style={{ marginLeft: 8 }}>
                    <span className={`ws-dot ${connected ? 'on' : 'off'}`} style={{ display: 'inline-block' }} />
                  </span>
                </strong>
                <button className="btn btn-sm btn-ghost" onClick={() => { clearMessages(); }}>Clear</button>
              </div>
              <div style={{ maxHeight: 300, overflowY: 'auto' }}>
                {messages.length === 0 ? (
                  <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                    No notifications yet
                  </div>
                ) : messages.map(m => (
                  <div key={m.id} style={{ padding: '10px 16px', borderBottom: '1px solid #f3f4f6', fontSize: '0.85rem' }}>
                    <div style={{ fontWeight: 500 }}>{m.message}</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.78rem', marginTop: 2 }}>{m.type}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-icon">👨‍⚕️</div>
          <div>
            <div className="stat-label">Total Doctors</div>
            <div className="stat-value">{stats.doctors}</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🏥</div>
          <div>
            <div className="stat-label">Total Patients</div>
            <div className="stat-value">{stats.patients}</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">📅</div>
          <div>
            <div className="stat-label">Appointments</div>
            <div className="stat-value">{stats.appointments}</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">⏳</div>
          <div>
            <div className="stat-label">Scheduled</div>
            <div className="stat-value" style={{ color: 'var(--info)' }}>{stats.scheduled}</div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="flex justify-between items-center" style={{ marginBottom: 16 }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem' }}>Recent Appointments</h3>
          <span className="text-muted">Last 5</span>
        </div>
        {recentAppointments.length === 0 ? (
          <div className="empty-state"><div className="icon">📅</div><div>No appointments yet</div></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th><th>Doctor</th><th>Patient</th><th>Date</th><th>Status</th>
                </tr>
              </thead>
              <tbody>
                {recentAppointments.map(a => (
                  <tr key={a.id}>
                    <td>#{a.id}</td>
                    <td>{a.doctor?.name || `Dr. #${a.doctor_id}`}</td>
                    <td>{a.patient?.name || `Patient #${a.patient_id}`}</td>
                    <td>{new Date(a.appointment_date).toLocaleDateString()}</td>
                    <td>{statusBadge(a.status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div style={{ marginTop: 16, display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-muted)', fontSize: '0.82rem' }}>
        <span className={`ws-dot ${connected ? 'on' : 'off'}`} />
        WebSocket {connected ? 'connected — receiving live updates' : 'disconnected — reconnecting...'}
      </div>
    </div>
  );
}
