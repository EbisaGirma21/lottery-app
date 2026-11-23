import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, Mail, ShieldCheck, Sparkles, Trophy } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('admin@lottery.com');
  const [password, setPassword] = useState('admin123456');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Invalid email or password. Please try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleDemoFill = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError(null);
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      background: 'var(--bg-app)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Left Branding Showcase */}
      <div style={{
        flex: 1,
        padding: '60px 80px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        background: 'linear-gradient(145deg, rgba(14, 19, 31, 0.95), rgba(8, 11, 17, 0.98))',
        borderRight: '1px solid var(--border-subtle)',
        position: 'relative'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '40px' }}>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, var(--primary), var(--emerald))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#FFF',
              boxShadow: '0 0 20px rgba(99, 102, 241, 0.4)'
            }}>
              <Sparkles size={24} />
            </div>
            <span style={{ fontFamily: 'Outfit', fontWeight: 800, fontSize: '1.4rem', color: '#FFF' }}>
              LOTTO<span style={{ color: 'var(--emerald)' }}>ADMIN</span>
            </span>
          </div>

          <h1 style={{ fontSize: '2.8rem', lineHeight: 1.15, marginBottom: '20px', maxWidth: '520px' }}>
            Enterprise Lottery & Prize Operations Platform
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem', maxWidth: '480px', lineHeight: 1.6 }}>
            Unified administrative control center for dynamic capacity lottery management,
            strict manual payment verification, and cryptographically verifiable random draws.
          </p>
        </div>

        {/* Highlight Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px', maxWidth: '540px' }}>
          <div style={{
            padding: '16px',
            background: 'rgba(255, 255, 255, 0.03)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)'
          }}>
            <ShieldCheck size={20} color="var(--emerald)" style={{ marginBottom: '8px' }} />
            <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#FFF' }}>Manual Bank Verification</div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              Staff inspection of Telebirr & bank receipts.
            </div>
          </div>

          <div style={{
            padding: '16px',
            background: 'rgba(255, 255, 255, 0.03)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)'
          }}>
            <Trophy size={20} color="var(--gold)" style={{ marginBottom: '8px' }} />
            <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#FFF' }}>SHA-256 Cryptographic Draw</div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              Tamper-proof 1st, 2nd, and 3rd prize engine.
            </div>
          </div>
        </div>

        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          © 2026 National Lottery Management System. All rights reserved.
        </div>
      </div>

      {/* Right Login Form */}
      <div style={{
        width: '520px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        padding: '60px',
        background: 'var(--bg-app)'
      }}>
        <div style={{ maxWidth: '400px', width: '100%', margin: '0 auto' }}>
          <div style={{ marginBottom: '32px' }}>
            <h2 style={{ fontSize: '1.8rem', marginBottom: '8px' }}>Staff Sign In</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem' }}>
              Enter your authorized staff credentials to continue.
            </p>
          </div>

          {error && (
            <div style={{
              padding: '12px 16px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--rose-surface)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#FCA5A5',
              fontSize: '0.88rem',
              marginBottom: '20px'
            }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Work Email</label>
              <div className="input-icon-wrapper">
                <Mail className="input-icon" size={18} />
                <input
                  type="email"
                  required
                  className="form-control input-with-icon"
                  placeholder="name@lottery.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: '24px' }}>
              <label className="form-label">Password</label>
              <div className="input-icon-wrapper">
                <Lock className="input-icon" size={18} />
                <input
                  type="password"
                  required
                  className="form-control input-with-icon"
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary btn-lg"
              style={{ width: '100%', marginBottom: '28px' }}
            >
              {loading ? 'Authenticating...' : 'Sign In to Portal'}
            </button>
          </form>

          {/* Demo Quick Fill Helper */}
          <div style={{
            padding: '16px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)'
          }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '10px' }}>
              Quick Demo Accounts
            </div>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => handleDemoFill('admin@lottery.com', 'admin123456')}
              >
                Super Admin
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => handleDemoFill('finance@lottery.com', 'admin123456')}
              >
                Payment Officer
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => handleDemoFill('draw@lottery.com', 'admin123456')}
              >
                Draw Officer
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
