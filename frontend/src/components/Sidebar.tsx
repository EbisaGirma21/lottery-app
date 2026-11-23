import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  CreditCard,
  FileBarChart,
  LayoutDashboard,
  LogOut,
  ShieldAlert,
  Sparkles,
  Ticket,
  Trophy,
  Users,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Sidebar: React.FC = () => {
  const { user, logout, isSuperAdmin, isPaymentVerifier, isDrawOfficer, isLotteryManager } = useAuth();

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div className="sidebar-header">
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #6366F1, #10B981)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#FFF',
          boxShadow: '0 0 16px rgba(99, 102, 241, 0.4)'
        }}>
          <Sparkles size={20} />
        </div>
        <div>
          <div style={{ fontFamily: 'Outfit', fontWeight: 800, fontSize: '1.1rem', letterSpacing: '-0.02em', color: '#FFF' }}>
            LOTTO<span style={{ color: 'var(--emerald)' }}>ADMIN</span>
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            National Lottery
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <NavLink to="/" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <LayoutDashboard size={18} />
          <span>Dashboard</span>
        </NavLink>

        {isLotteryManager && (
          <NavLink to="/lotteries" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Ticket size={18} />
            <span>Lotteries</span>
          </NavLink>
        )}

        {(isLotteryManager || isPaymentVerifier) && (
          <NavLink to="/participants" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Users size={18} />
            <span>Applicants</span>
          </NavLink>
        )}

        {isPaymentVerifier && (
          <NavLink to="/payments" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <CreditCard size={18} />
            <span>Payment Queue</span>
          </NavLink>
        )}

        {isDrawOfficer && (
          <NavLink to="/draws" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Trophy size={18} />
            <span>Draw Engine</span>
          </NavLink>
        )}

        <NavLink to="/reports" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <FileBarChart size={18} />
          <span>Reports & Analytics</span>
        </NavLink>

        {isSuperAdmin && (
          <NavLink to="/audit-logs" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <ShieldAlert size={18} />
            <span>Audit Trail</span>
          </NavLink>
        )}
      </nav>

      {/* User Footer */}
      <div className="sidebar-footer">
        <div className="user-badge" style={{ marginBottom: '10px' }}>
          <div className="user-avatar">
            {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#FFF', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {user?.full_name || 'Staff User'}
            </div>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
              {user?.role.replace('_', ' ')}
            </div>
          </div>
        </div>

        <button
          onClick={logout}
          className="btn btn-secondary btn-sm"
          style={{ width: '100%', justifyContent: 'flex-start' }}
        >
          <LogOut size={16} />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
};
