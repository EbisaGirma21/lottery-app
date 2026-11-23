import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  Clock,
  CreditCard,
  DollarSign,
  FileCheck,
  Plus,
  RefreshCw,
  Sparkles,
  Ticket,
  Trophy,
} from 'lucide-react';
import { reportsApi } from '../api/reports';
import { DashboardAnalytics } from '../api/types';
import { useAuth } from '../context/AuthContext';

export const Dashboard: React.FC = () => {
  const [data, setData] = useState<DashboardAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const { isLotteryManager, isPaymentVerifier, isDrawOfficer } = useAuth();

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const analytics = await reportsApi.getDashboardAnalytics();
      setData(analytics);
    } catch (err) {
      console.error('Error loading dashboard analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  if (loading && !data) {
    return (
      <div style={{ padding: '60px 0', textAlign: 'center', color: 'var(--text-secondary)' }}>
        <RefreshCw size={32} className="spin" style={{ margin: '0 auto 16px' }} />
        <p>Loading real-time lottery analytics...</p>
      </div>
    );
  }

  return (
    <div>
      {/* Top Banner Actions */}
      <div className="flex-between" style={{ marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', marginBottom: '4px' }}>Executive Operations Dashboard</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Real-time financial metrics, dynamic ticket sales velocity, and verification review queues.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button onClick={fetchDashboard} className="btn btn-secondary btn-sm" title="Refresh metrics">
            <RefreshCw size={16} />
            <span>Refresh</span>
          </button>
          {isLotteryManager && (
            <Link to="/lotteries" className="btn btn-primary btn-sm">
              <Plus size={16} />
              <span>New Lottery</span>
            </Link>
          )}
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="stat-grid">
        <div className="stat-card" style={{ '--stat-accent': 'var(--emerald)' } as React.CSSProperties}>
          <div>
            <div className="stat-label">Total Verified Revenue</div>
            <div className="stat-value" style={{ color: 'var(--emerald)' }}>
              {Number(data?.total_revenue || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })} <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>ETB</span>
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '8px' }}>
              This Month: <b>{Number(data?.monthly_revenue || 0).toLocaleString()} ETB</b>
            </div>
          </div>
          <div style={{ padding: '10px', borderRadius: '10px', background: 'var(--emerald-surface)', color: 'var(--emerald)' }}>
            <DollarSign size={24} />
          </div>
        </div>

        <div className="stat-card" style={{ '--stat-accent': 'var(--amber)' } as React.CSSProperties}>
          <div>
            <div className="stat-label">Manual Verification Queue</div>
            <div className="stat-value" style={{ color: 'var(--amber)' }}>
              {data?.pending_payments_count || 0} <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>orders</span>
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '8px' }}>
              Awaiting Review: <b>{Number(data?.pending_payments_value || 0).toLocaleString()} ETB</b>
            </div>
          </div>
          <div style={{ padding: '10px', borderRadius: '10px', background: 'var(--amber-surface)', color: 'var(--amber)' }}>
            <Clock size={24} />
          </div>
        </div>

        <div className="stat-card" style={{ '--stat-accent': 'var(--primary)' } as React.CSSProperties}>
          <div>
            <div className="stat-label">Total Sold Tickets</div>
            <div className="stat-value" style={{ color: 'var(--primary)' }}>
              {data?.total_tickets_sold?.toLocaleString() || 0}
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '8px' }}>
              Conversion Rate: <b>{data?.overall_conversion_rate || 0}%</b>
            </div>
          </div>
          <div style={{ padding: '10px', borderRadius: '10px', background: 'var(--primary-surface)', color: 'var(--primary)' }}>
            <Ticket size={24} />
          </div>
        </div>

        <div className="stat-card" style={{ '--stat-accent': 'var(--cyan)' } as React.CSSProperties}>
          <div>
            <div className="stat-label">Active Lotteries</div>
            <div className="stat-value" style={{ color: 'var(--cyan)' }}>
              {data?.active_lotteries_count || 0}
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '8px' }}>
              Currently accepting ticket sales
            </div>
          </div>
          <div style={{ padding: '10px', borderRadius: '10px', background: 'var(--cyan-surface)', color: 'var(--cyan)' }}>
            <Trophy size={24} />
          </div>
        </div>
      </div>

      {/* Grid: Payment Method Breakdown & Quick Actions */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px', marginBottom: '32px' }}>
        {/* Revenue by Payment Method */}
        <div className="card">
          <div className="flex-between" style={{ marginBottom: '20px' }}>
            <h3 style={{ fontSize: '1.15rem' }}>Revenue Breakdown by Payment Channel</h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Verified Bank Ledger</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {(data?.revenue_by_method || []).map((item) => {
              const totalNum = Number(data?.total_revenue || 1);
              const itemNum = Number(item.total);
              const pct = totalNum > 0 ? Math.round((itemNum / totalNum) * 100) : 0;

              return (
                <div key={item.method}>
                  <div className="flex-between" style={{ marginBottom: '6px', fontSize: '0.88rem' }}>
                    <span style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <CreditCard size={16} color="var(--primary)" />
                      {item.display_name}
                    </span>
                    <span style={{ color: 'var(--text-secondary)' }}>
                      <b>{itemNum.toLocaleString('en-US', { minimumFractionDigits: 2 })} ETB</b> ({item.count} orders · {pct}%)
                    </span>
                  </div>
                  <div style={{ height: '8px', borderRadius: '4px', background: 'var(--bg-surface-elevated)', overflow: 'hidden' }}>
                    <div
                      style={{
                        height: '100%',
                        width: `${pct}%`,
                        background: 'linear-gradient(90deg, var(--primary), var(--emerald))',
                        borderRadius: '4px',
                        transition: 'width 0.5s ease-out',
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Quick Operations Portal */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', marginBottom: '16px' }}>Quick Operations</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '20px' }}>
              Direct access to critical workflows across manual verification and draws.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {isPaymentVerifier && (
                <Link to="/payments" className="btn btn-secondary" style={{ justifyContent: 'space-between' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FileCheck size={18} color="var(--amber)" />
                    <span>Review Pending Payments</span>
                  </span>
                  <ArrowRight size={16} />
                </Link>
              )}

              {isDrawOfficer && (
                <Link to="/draws" className="btn btn-secondary" style={{ justifyContent: 'space-between' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Sparkles size={18} color="var(--primary)" />
                    <span>Run Cryptographic Draw</span>
                  </span>
                  <ArrowRight size={16} />
                </Link>
              )}

              <Link to="/reports" className="btn btn-secondary" style={{ justifyContent: 'space-between' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <DollarSign size={18} color="var(--emerald)" />
                  <span>Download Excel & PDF Reports</span>
                </span>
                <ArrowRight size={16} />
              </Link>
            </div>
          </div>

          <div style={{
            padding: '12px 16px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.78rem',
            color: 'var(--text-muted)',
            marginTop: '20px'
          }}>
            🔒 <b>Zero-Fraud Policy:</b> Authorized staff verify every manual transaction against bank statements before ticket issuance.
          </div>
        </div>
      </div>

      {/* Recent Payments Section */}
      <div className="card" style={{ marginBottom: '32px' }}>
        <div className="flex-between" style={{ marginBottom: '20px' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem' }}>Recent Payment Submissions</h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Latest transactions across all lotteries</span>
          </div>
          <Link to="/payments" className="btn btn-outline btn-sm">
            View All Payments
          </Link>
        </div>

        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Reference</th>
                <th>Customer</th>
                <th>Lottery</th>
                <th>Method</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Submitted</th>
              </tr>
            </thead>
            <tbody>
              {(data?.recent_payments || []).length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                    No payment submissions yet.
                  </td>
                </tr>
              ) : (
                (data?.recent_payments || []).slice(0, 6).map((payment: any) => {
                  const customerName = payment.customer?.full_name || payment.customer__full_name || 'Anonymous';
                  const customerPhone = payment.customer?.phone_number || payment.customer__phone_number || '';
                  const lotteryName = payment.lottery?.name || payment.lottery__name || 'Lottery';
                  const rawDate = payment.submitted_at || payment.reviewed_at || payment.created_at;
                  const formattedDate = rawDate ? new Date(rawDate).toLocaleDateString() : '—';

                  return (
                    <tr key={payment.id}>
                      <td>
                        <code style={{ color: 'var(--primary)', fontWeight: 600 }}>
                          {payment.transaction_reference}
                        </code>
                      </td>
                      <td>
                        <div>{customerName}</div>
                        {customerPhone && (
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            {customerPhone}
                          </div>
                        )}
                      </td>
                      <td>{lotteryName}</td>
                      <td style={{ textTransform: 'uppercase', fontSize: '0.8rem' }}>
                        {payment.payment_method}
                      </td>
                      <td style={{ fontWeight: 600 }}>{payment.amount} ETB</td>
                      <td>
                        <span className={`badge badge-${payment.status || 'pending'}`}>
                          {payment.status || 'pending'}
                        </span>
                      </td>
                      <td style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                        {formattedDate}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
