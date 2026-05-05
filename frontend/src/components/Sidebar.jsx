import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from './Toast';

const navConfig = {
  admin: [
    { section: 'Overview' },
    { path: '/', label: 'Dashboard', icon: '🏠' },
    { section: 'Management' },
    { path: '/doctors', label: 'Doctors', icon: '👨‍⚕️' },
    { path: '/patients', label: 'Patients', icon: '🧑‍🤝‍🧑' },
    { path: '/appointments', label: 'Appointments', icon: '📅' },
  ],
  doctor: [
    { section: 'Overview' },
    { path: '/', label: 'Dashboard', icon: '🏠' },
    { path: '/appointments', label: 'Appointments', icon: '📅' },
  ],
  patient: [
    { section: 'Overview' },
    { path: '/', label: 'Dashboard', icon: '🏠' },
    { path: '/appointments', label: 'My Appointments', icon: '📅' },
  ],
};

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const toast = useToast();

  const navItems = navConfig[user?.role] || [];

  const handleLogout = () => {
    logout();
    toast("Logged out successfully", "success");
    navigate('/login');
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>Med<span>Core</span></h1>
        <p>Hospital System</p>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item, i) => {
          if (item.section) {
            return <div key={i} className="nav-section">{item.section}</div>;
          }

          const active = item.path === '/'
            ? location.pathname === '/'
            : location.pathname.startsWith(item.path);

          return (
            <button
              key={item.path}
              className={`nav-link ${active ? 'active' : ''}`}
              onClick={() => navigate(item.path)}
            >
              <span className="icon">{item.icon}</span>
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="user-chip" onClick={handleLogout} title="Click to logout">
          <div className="user-avatar">
            {user?.username?.[0]?.toUpperCase()}
          </div>
          <div className="user-chip-info">
            <div className="user-chip-name">{user?.username}</div>
            <div className="user-chip-role">{user?.role}</div>
          </div>
          <button className="logout-btn">⏻</button>
        </div>
      </div>
    </aside>
  );
}