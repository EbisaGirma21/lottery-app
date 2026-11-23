import React from 'react';
import { Bell, Shield } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface TopbarProps {
  title?: string;
}

export const Topbar: React.FC<TopbarProps> = ({ title }) => {
  const { user } = useAuth();

  return (
    <header className="topbar">
      <div>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0 }}>
          {title || 'Lottery Operations Command Center'}
        </h2>
      </div>

      <div style={{ display: 'flex', alignContent: 'center', alignItems: 'center', gap: '16px' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '4px 10px',
          borderRadius: '20px',
          background: 'rgba(99, 102, 241, 0.1)',
          border: '1px solid rgba(99, 102, 241, 0.25)',
          color: 'var(--primary)',
          fontSize: '0.78rem',
          fontWeight: 600,
          textTransform: 'uppercase'
        }}>
          <Shield size={14} />
          <span>{user?.role.replace('_', ' ')}</span>
        </div>

        <div style={{
          position: 'relative',
          padding: '8px',
          borderRadius: '50%',
          background: 'var(--bg-surface-elevated)',
          border: '1px solid var(--border-subtle)',
          cursor: 'pointer',
          color: 'var(--text-secondary)'
        }}>
          <Bell size={18} />
          <span style={{
            position: 'absolute',
            top: '6px',
            right: '6px',
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: 'var(--emerald)'
          }} />
        </div>
      </div>
    </header>
  );
};
