import React, { useEffect, useState } from 'react';
import {
  Clock,
  ExternalLink,
  Eye,
  Filter,
  RefreshCw,
  Search,
} from 'lucide-react';
import { paymentsApi } from '../api/payments';
import { Payment } from '../api/types';
import { PaymentInspectionModal } from './PaymentInspectionModal';

export const PaymentQueue: React.FC = () => {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [stats, setStats] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('pending');
  const [methodFilter, setMethodFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPayment, setSelectedPayment] = useState<Payment | null>(null);

  const fetchQueue = async () => {
    setLoading(true);
    try {
      const params: Record<string, any> = {};
      if (statusFilter !== 'all') params.status = statusFilter;
      if (methodFilter !== 'all') params.payment_method = methodFilter;
      if (searchQuery) params.search = searchQuery;

      const [res, statsRes] = await Promise.all([
        paymentsApi.getPayments(params),
        paymentsApi.getStats(),
      ]);
      setPayments(res.results);
      setStats(statsRes);
    } catch (err) {
      console.error('Error fetching payments queue:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, [statusFilter, methodFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchQueue();
  };

  return (
    <div>
      {/* Header */}
      <div className="flex-between" style={{ marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', marginBottom: '4px' }}>Manual Payment Verification Queue</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Authorized finance staff inspect customer payment references against official bank records.
          </p>
        </div>

        <button onClick={fetchQueue} className="btn btn-secondary btn-sm">
          <RefreshCw size={16} />
          <span>Refresh Queue</span>
        </button>
      </div>

      {/* Live Queue Banner */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <div style={{
          padding: '16px 20px',
          borderRadius: 'var(--radius-md)',
          background: 'var(--amber-surface)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          display: 'flex',
          alignItems: 'center',
          gap: '14px'
        }}>
          <Clock size={28} color="var(--amber)" />
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--amber)', fontWeight: 600, textTransform: 'uppercase' }}>
              Pending Verification
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#FFF' }}>
              {stats?.pending_count || 0} <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>orders</span>
            </div>
          </div>
        </div>

        <div style={{
          padding: '16px 20px',
          borderRadius: 'var(--radius-md)',
          background: 'var(--emerald-surface)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          display: 'flex',
          alignItems: 'center',
          gap: '14px'
        }}>
          <Clock size={28} color="var(--emerald)" />
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--emerald)', fontWeight: 600, textTransform: 'uppercase' }}>
              Approved Total Value
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#FFF' }}>
              {Number(stats?.total_approved_amount || 0).toLocaleString()} <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>ETB</span>
            </div>
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="card" style={{ padding: '16px 20px', marginBottom: '24px' }}>
        <div className="flex-between" style={{ flexWrap: 'wrap', gap: '16px' }}>
          {/* Status Tabs */}
          <div style={{ display: 'flex', gap: '8px' }}>
            {[
              { id: 'pending', label: 'Pending Review' },
              { id: 'approved', label: 'Approved' },
              { id: 'rejected', label: 'Rejected' },
              { id: 'all', label: 'All Payments' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setStatusFilter(tab.id)}
                className={`btn btn-sm ${statusFilter === tab.id ? 'btn-primary' : 'btn-secondary'}`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Method and Search Filters */}
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Filter size={16} color="var(--text-muted)" />
              <select
                className="form-select"
                style={{ padding: '6px 12px', fontSize: '0.85rem', width: '160px' }}
                value={methodFilter}
                onChange={(e) => setMethodFilter(e.target.value)}
              >
                <option value="all">All Channels</option>
                <option value="telebirr">Telebirr</option>
                <option value="cbe">CBE</option>
                <option value="cbe_birr">CBE Birr</option>
                <option value="awash">Awash Bank</option>
                <option value="boa">Bank of Abyssinia</option>
                <option value="other">Other</option>
              </select>
            </div>

            <form onSubmit={handleSearch} style={{ display: 'flex', gap: '8px' }}>
              <div className="input-icon-wrapper" style={{ width: '220px' }}>
                <Search className="input-icon" size={14} />
                <input
                  type="text"
                  className="form-control input-with-icon"
                  style={{ padding: '6px 10px 6px 34px', fontSize: '0.85rem' }}
                  placeholder="Search reference..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <button type="submit" className="btn btn-secondary btn-sm">
                Filter
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Queue Table */}
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Reference Code</th>
              <th>Customer</th>
              <th>Lottery</th>
              <th>Channel</th>
              <th>Amount</th>
              <th>Proof</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
                  <RefreshCw size={24} className="spin" style={{ margin: '0 auto 8px' }} />
                  <div>Loading verification queue...</div>
                </td>
              </tr>
            ) : payments.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  No payments found in this queue.
                </td>
              </tr>
            ) : (
              payments.map((p) => (
                <tr key={p.id}>
                  <td>
                    <code style={{ fontWeight: 700, color: 'var(--primary)' }}>
                      {p.transaction_reference}
                    </code>
                  </td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{p.customer.full_name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {p.customer.phone_number || `@${p.customer.telegram_username || 'Telegram'}`}
                    </div>
                  </td>
                  <td>{p.lottery.name}</td>
                  <td>
                    {p.payment_method.toLowerCase().includes('telebirr') ? (
                      <span
                        style={{
                          padding: '3px 7px',
                          borderRadius: '4px',
                          background: 'rgba(6, 182, 212, 0.15)',
                          border: '1px solid rgba(6, 182, 212, 0.35)',
                          color: '#38BDF8',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          display: 'inline-block',
                        }}
                      >
                        📱 Telebirr
                      </span>
                    ) : p.payment_method.toLowerCase().includes('cbe') ? (
                      <span
                        style={{
                          padding: '3px 7px',
                          borderRadius: '4px',
                          background: 'rgba(168, 85, 247, 0.15)',
                          border: '1px solid rgba(168, 85, 247, 0.35)',
                          color: '#C084FC',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          display: 'inline-block',
                        }}
                      >
                        🏦 CBE
                      </span>
                    ) : (
                      <span style={{ textTransform: 'uppercase', fontSize: '0.8rem', fontWeight: 600 }}>
                        {p.payment_method}
                      </span>
                    )}
                  </td>
                  <td style={{ fontWeight: 700, color: 'var(--emerald)' }}>
                    {p.amount} ETB
                  </td>
                  <td>
                    {p.payment_proof ? (
                      <div
                        onClick={() => setSelectedPayment(p)}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          cursor: 'pointer',
                        }}
                        title="Click to inspect receipt screenshot"
                      >
                        <div
                          style={{
                            width: '36px',
                            height: '36px',
                            borderRadius: '4px',
                            overflow: 'hidden',
                            border: '1px solid var(--border-prominent)',
                            background: '#000',
                          }}
                        >
                          <img
                            src={p.payment_proof}
                            alt="Receipt proof"
                            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                          />
                        </div>
                        <span
                          style={{
                            fontSize: '0.75rem',
                            color: 'var(--cyan)',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '2px',
                            textDecoration: 'underline',
                          }}
                        >
                          <Eye size={13} />
                          Receipt
                        </span>
                      </div>
                    ) : (
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>None</span>
                    )}
                  </td>
                  <td>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', alignItems: 'flex-start' }}>
                      <span className={`badge badge-${p.status}`}>
                        {p.status}
                      </span>
                      {p.is_auto_verified && (
                        <span
                          style={{
                            fontSize: '0.68rem',
                            fontWeight: 700,
                            padding: '1px 5px',
                            borderRadius: '3px',
                            background: 'rgba(16, 185, 129, 0.15)',
                            border: '1px solid rgba(16, 185, 129, 0.4)',
                            color: '#10B981',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '2px',
                          }}
                          title="Confirmed against bank records via REST API"
                        >
                          ⚡ Auto-Verified
                        </span>
                      )}
                      {!p.is_auto_verified && p.auto_verification_status === 'FAILED' && (
                        <span
                          style={{
                            fontSize: '0.66rem',
                            fontWeight: 600,
                            padding: '1px 4px',
                            borderRadius: '3px',
                            background: 'rgba(239, 68, 68, 0.12)',
                            border: '1px solid rgba(239, 68, 68, 0.3)',
                            color: '#EF4444',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '2px',
                          }}
                          title={p.verification_error || 'Automated bank check could not confirm'}
                        >
                          ⚠️ Unconfirmed
                        </span>
                      )}
                    </div>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      onClick={() => setSelectedPayment(p)}
                      className={`btn btn-sm ${p.status === 'pending' ? 'btn-primary' : 'btn-secondary'}`}
                    >
                      <span>{p.status === 'pending' ? 'Verify & Review' : 'Details'}</span>
                      <ExternalLink size={14} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Verification Modal */}
      <PaymentInspectionModal
        payment={selectedPayment}
        isOpen={!!selectedPayment}
        onClose={() => setSelectedPayment(null)}
        onActionComplete={fetchQueue}
      />
    </div>
  );
};
