import React, { useEffect, useMemo, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  CreditCard,
  ExternalLink,
  Eye,
  FileText,
  Filter,
  Image as ImageIcon,
  Phone,
  RefreshCw,
  Search,
  Send,
  Ticket as TicketIcon,
  User as UserIcon,
  Users,
  X,
  XCircle,
} from 'lucide-react';
import { lotteriesApi } from '../api/lotteries';
import { paymentsApi } from '../api/payments';
import {
  ApplicationStatus,
  Lottery,
  LotteryParticipant,
  Payment,
} from '../api/types';
import { PaymentInspectionModal } from './PaymentInspectionModal';

export const Participants: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const lotteryIdFromUrl = searchParams.get('lottery');

  const [lotteries, setLotteries] = useState<Lottery[]>([]);
  const [selectedLotteryId, setSelectedLotteryId] = useState<string>(lotteryIdFromUrl || '');
  const [participants, setParticipants] = useState<LotteryParticipant[]>([]);
  const [lotteryName, setLotteryName] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [lotteriesLoading, setLotteriesLoading] = useState<boolean>(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [channelFilter, setChannelFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Modals & Lightbox
  const [selectedPayment, setSelectedPayment] = useState<Payment | null>(null);
  const [inspectLoading, setInspectLoading] = useState<boolean>(false);
  const [activeLightboxImg, setActiveLightboxImg] = useState<{ url: string; title: string } | null>(null);

  // Fetch all available lotteries for the selector
  useEffect(() => {
    const fetchLotteries = async () => {
      setLotteriesLoading(true);
      try {
        const res = await lotteriesApi.getLotteries();
        setLotteries(res.results);

        // If no lottery selected in URL, pick the first active/open lottery or first available
        if (!selectedLotteryId && res.results.length > 0) {
          const defaultLottery =
            res.results.find((l) => l.status === 'open') ||
            res.results.find((l) => l.status === 'paused') ||
            res.results[0];
          setSelectedLotteryId(defaultLottery.id);
        }
      } catch (err) {
        console.error('Failed to fetch lotteries:', err);
      } finally {
        setLotteriesLoading(false);
      }
    };
    fetchLotteries();
  }, []);

  // When lottery selection changes, update URL and fetch participants
  useEffect(() => {
    if (!selectedLotteryId) return;

    setSearchParams({ lottery: selectedLotteryId });
    fetchParticipants(selectedLotteryId);
  }, [selectedLotteryId]);

  const fetchParticipants = async (lotteryId: string) => {
    setLoading(true);
    try {
      const res = await lotteriesApi.getParticipants(lotteryId);
      setParticipants(res.participants || []);
      setLotteryName(res.lottery_name || 'Lottery');
    } catch (err) {
      console.error('Failed to fetch lottery participants:', err);
      setParticipants([]);
    } finally {
      setLoading(false);
    }
  };

  // Open Payment Verification Modal by fetching full payment object
  const handleOpenInspection = async (paymentId: string) => {
    setInspectLoading(true);
    try {
      const p = await paymentsApi.getPayment(paymentId);
      setSelectedPayment(p);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to fetch payment details.');
    } finally {
      setInspectLoading(false);
    }
  };

  // Filtered participants calculation
  const filteredParticipants = useMemo(() => {
    return participants.filter((p) => {
      // Status filter
      if (statusFilter !== 'all' && p.application_status !== statusFilter) {
        return false;
      }

      // Channel filter
      if (channelFilter !== 'all') {
        const hasMatchingChannel = p.payments.some((pay) =>
          pay.payment_method.toLowerCase().includes(channelFilter.toLowerCase())
        );
        if (!hasMatchingChannel) return false;
      }

      // Search query (matches name, phone, telegram username, or ticket number)
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const matchName = (p.full_name || '').toLowerCase().includes(q);
        const matchPhone = (p.phone_number || '').toLowerCase().includes(q);
        const matchTg = (p.telegram_username || '').toLowerCase().includes(q);
        const matchSold = p.tickets_sold.some((t) => t.toLowerCase().includes(q));
        const matchReserved = p.tickets_reserved.some((t) => t.toLowerCase().includes(q));
        const matchRef = p.payments.some((pay) =>
          (pay.transaction_reference || '').toLowerCase().includes(q)
        );

        if (!matchName && !matchPhone && !matchTg && !matchSold && !matchReserved && !matchRef) {
          return false;
        }
      }

      return true;
    });
  }, [participants, statusFilter, channelFilter, searchQuery]);

  // Compute stats for the current lottery
  const stats = useMemo(() => {
    const totalApplicants = participants.length;
    let pendingReviews = 0;
    let totalSoldTickets = 0;
    let totalReservedTickets = 0;
    let verifiedRevenue = 0;

    participants.forEach((p) => {
      totalSoldTickets += p.tickets_sold.length;
      totalReservedTickets += p.tickets_reserved.length;

      p.payments.forEach((pay) => {
        if (pay.status === 'pending') {
          pendingReviews += 1;
        } else if (pay.status === 'approved') {
          verifiedRevenue += parseFloat(pay.amount || '0');
        }
      });
    });

    return {
      totalApplicants,
      pendingReviews,
      totalSoldTickets,
      totalReservedTickets,
      verifiedRevenue,
    };
  }, [participants]);

  const selectedLotteryObj = lotteries.find((l) => l.id === selectedLotteryId);

  return (
    <div>
      {/* Top Header & Lottery Switcher */}
      <div className="flex-between" style={{ marginBottom: '20px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, var(--primary), var(--emerald))',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#FFF',
              }}
            >
              <Users size={20} />
            </div>
            <div>
              <h1 style={{ fontSize: '1.65rem', marginBottom: '2px' }}>
                Lottery Applicants & Verification
              </h1>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.86rem' }}>
                User list based on lottery applications. Inspect uploaded receipt screenshots (Telebirr / CBE) and verify payments.
              </p>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          {/* Lottery Selector Dropdown */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
              Lottery:
            </span>
            <select
              className="form-control"
              style={{
                width: '240px',
                padding: '8px 12px',
                fontSize: '0.85rem',
                fontWeight: 600,
                background: 'var(--bg-surface-elevated)',
                borderColor: 'var(--border-prominent)',
              }}
              value={selectedLotteryId}
              onChange={(e) => setSelectedLotteryId(e.target.value)}
              disabled={lotteriesLoading || lotteries.length === 0}
            >
              {lotteries.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name} ({l.status.toUpperCase()})
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => selectedLotteryId && fetchParticipants(selectedLotteryId)}
            className="btn btn-secondary btn-sm"
            disabled={loading}
          >
            <RefreshCw size={15} className={loading ? 'spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Selected Lottery Details Summary Banner */}
      {selectedLotteryObj && (
        <div
          style={{
            padding: '12px 18px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-subtle)',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span className={`badge badge-${selectedLotteryObj.status}`}>
              {selectedLotteryObj.status}
            </span>
            <span style={{ fontWeight: 700, fontSize: '1rem', color: '#FFF' }}>
              {selectedLotteryObj.name}
            </span>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
              Ticket Price: <b style={{ color: 'var(--emerald)' }}>{selectedLotteryObj.ticket_price} ETB</b>
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '0.82rem' }}>
            <Link
              to={`/payments?lottery=${selectedLotteryId}`}
              style={{
                color: 'var(--primary)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                textDecoration: 'none',
              }}
            >
              <CreditCard size={14} />
              <span>Full Payment Queue</span>
              <ArrowRight size={12} />
            </Link>
          </div>
        </div>
      )}

      {/* KPI Metric Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          marginBottom: '24px',
        }}
      >
        {/* Total Applicants */}
        <div
          style={{
            padding: '16px 20px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
          }}
        >
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              background: 'rgba(99, 102, 241, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--primary)',
            }}
          >
            <Users size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Total Applicants
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#FFF' }}>
              {stats.totalApplicants}
            </div>
          </div>
        </div>

        {/* Pending Verification */}
        <div
          style={{
            padding: '16px 20px',
            borderRadius: 'var(--radius-md)',
            background: stats.pendingReviews > 0 ? 'var(--amber-surface)' : 'var(--bg-surface-elevated)',
            border: stats.pendingReviews > 0 ? '1px solid rgba(245, 158, 11, 0.4)' : '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
          }}
        >
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              background: stats.pendingReviews > 0 ? 'rgba(245, 158, 11, 0.25)' : 'rgba(255, 255, 255, 0.05)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--amber)',
            }}
          >
            <Clock size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: stats.pendingReviews > 0 ? 'var(--amber)' : 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Pending Verification
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#FFF' }}>
              {stats.pendingReviews}
              {stats.pendingReviews > 0 && (
                <span style={{ fontSize: '0.75rem', color: 'var(--amber)', marginLeft: '6px' }}>
                  (Action required)
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Confirmed / Sold Tickets */}
        <div
          style={{
            padding: '16px 20px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
          }}
        >
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              background: 'rgba(16, 185, 129, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--emerald)',
            }}
          >
            <CheckCircle2 size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Confirmed Sold Tickets
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--emerald)' }}>
              {stats.totalSoldTickets}
            </div>
          </div>
        </div>

        {/* Reserved Unpaid */}
        <div
          style={{
            padding: '16px 20px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
          }}
        >
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              background: 'rgba(6, 182, 212, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--cyan)',
            }}
          >
            <TicketIcon size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Reserved Unpaid
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#FFF' }}>
              {stats.totalReservedTickets}
            </div>
          </div>
        </div>

        {/* Total Verified Revenue */}
        <div
          style={{
            padding: '16px 20px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
          }}
        >
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              background: 'rgba(234, 179, 8, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--gold)',
            }}
          >
            <CreditCard size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Verified Revenue
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--gold)' }}>
              {stats.verifiedRevenue.toLocaleString()} <span style={{ fontSize: '0.8rem' }}>ETB</span>
            </div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="card" style={{ padding: '16px 20px', marginBottom: '20px' }}>
        <div className="flex-between" style={{ flexWrap: 'wrap', gap: '14px' }}>
          {/* Status Tabs */}
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {[
              { key: 'all', label: 'All Applicants' },
              { key: 'pending_verification', label: `Pending Verification (${stats.pendingReviews})` },
              { key: 'approved_paid', label: 'Approved / Paid' },
              { key: 'reserved_unpaid', label: 'Reserved Unpaid' },
              { key: 'rejected', label: 'Rejected' },
            ].map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => setStatusFilter(tab.key)}
                className={`btn btn-sm ${statusFilter === tab.key ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.8rem' }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Channels & Search Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            {/* Channel filter */}
            <select
              className="form-control"
              style={{
                width: '150px',
                padding: '6px 10px',
                fontSize: '0.82rem',
                background: 'var(--bg-app)',
              }}
              value={channelFilter}
              onChange={(e) => setChannelFilter(e.target.value)}
            >
              <option value="all">All Channels</option>
              <option value="telebirr">Telebirr 📱</option>
              <option value="cbe">CBE Bank 🏦</option>
              <option value="cbe_birr">CBE Birr 📲</option>
            </select>

            {/* Search Input */}
            <div className="input-icon-wrapper" style={{ width: '260px' }}>
              <Search className="input-icon" size={15} />
              <input
                type="text"
                className="form-control input-with-icon"
                style={{ padding: '6px 10px 6px 34px', fontSize: '0.82rem' }}
                placeholder="Search name, phone, ticket #, ref..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Participants Table */}
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Applicant / User</th>
              <th>Status</th>
              <th>Tickets Applied</th>
              <th>Channel</th>
              <th>Amount</th>
              <th>Receipt Proof (Screenshot)</th>
              <th>Reference Code</th>
              <th style={{ textAlign: 'right' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '48px', color: 'var(--text-secondary)' }}>
                  <RefreshCw size={24} className="spin" style={{ margin: '0 auto 8px' }} />
                  <div>Loading lottery applicants...</div>
                </td>
              </tr>
            ) : filteredParticipants.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
                  <Users size={36} style={{ margin: '0 auto 10px', opacity: 0.3 }} />
                  <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>No applicants match this criteria.</div>
                  <div style={{ fontSize: '0.82rem', marginTop: '4px' }}>
                    Try adjusting the search query or status filter.
                  </div>
                </td>
              </tr>
            ) : (
              filteredParticipants.map((p) => {
                // Find primary pending payment or most recent payment
                const pendingPayment = p.payments.find((pay) => pay.status === 'pending');
                const latestPayment = pendingPayment || p.payments[0];

                const isTelebirr =
                  latestPayment?.payment_method.toLowerCase().includes('telebirr');
                const isCBE =
                  latestPayment?.payment_method.toLowerCase().includes('cbe');

                return (
                  <tr key={p.customer_id}>
                    {/* Customer */}
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div
                          style={{
                            width: '34px',
                            height: '34px',
                            borderRadius: '50%',
                            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(16, 185, 129, 0.3))',
                            border: '1px solid var(--border-prominent)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontWeight: 700,
                            color: '#FFF',
                            fontSize: '0.85rem',
                          }}
                        >
                          {p.full_name ? p.full_name.charAt(0).toUpperCase() : 'U'}
                        </div>
                        <div>
                          <div style={{ fontWeight: 600, color: '#FFF' }}>{p.full_name}</div>
                          <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', display: 'flex', gap: '8px' }}>
                            {p.phone_number && (
                              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
                                <Phone size={10} /> {p.phone_number}
                              </span>
                            )}
                            {p.telegram_username && (
                              <span style={{ color: 'var(--cyan)' }}>
                                @{p.telegram_username}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* Status Badge */}
                    <td>
                      {p.application_status === 'pending_verification' && (
                        <span
                          className="badge"
                          style={{
                            background: 'rgba(245, 158, 11, 0.2)',
                            color: '#FBBF24',
                            border: '1px solid rgba(245, 158, 11, 0.4)',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                          }}
                        >
                          <Clock size={12} />
                          Pending Review
                        </span>
                      )}
                      {p.application_status === 'approved_paid' && (
                        <span
                          className="badge"
                          style={{
                            background: 'rgba(16, 185, 129, 0.2)',
                            color: '#34D399',
                            border: '1px solid rgba(16, 185, 129, 0.4)',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                          }}
                        >
                          <CheckCircle2 size={12} />
                          Approved & Paid
                        </span>
                      )}
                      {p.application_status === 'reserved_unpaid' && (
                        <span
                          className="badge"
                          style={{
                            background: 'rgba(6, 182, 212, 0.2)',
                            color: '#38BDF8',
                            border: '1px solid rgba(6, 182, 212, 0.4)',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                          }}
                        >
                          <TicketIcon size={12} />
                          Reserved Unpaid
                        </span>
                      )}
                      {p.application_status === 'rejected' && (
                        <span
                          className="badge"
                          style={{
                            background: 'rgba(239, 68, 68, 0.2)',
                            color: '#F87171',
                            border: '1px solid rgba(239, 68, 68, 0.4)',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                          }}
                        >
                          <XCircle size={12} />
                          Rejected
                        </span>
                      )}
                      {p.application_status === 'in_progress' && (
                        <span className="badge badge-draft">In Progress</span>
                      )}
                    </td>

                    {/* Tickets Applied */}
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        {p.tickets_sold.length > 0 && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flexWrap: 'wrap' }}>
                            <span style={{ fontSize: '0.72rem', color: 'var(--emerald)', fontWeight: 600 }}>
                              Sold ({p.tickets_sold.length}):
                            </span>
                            {p.tickets_sold.slice(0, 4).map((t) => (
                              <span
                                key={t}
                                style={{
                                  padding: '2px 6px',
                                  borderRadius: '4px',
                                  background: 'rgba(16, 185, 129, 0.15)',
                                  border: '1px solid rgba(16, 185, 129, 0.3)',
                                  fontFamily: 'monospace',
                                  fontSize: '0.75rem',
                                  fontWeight: 600,
                                  color: '#34D399',
                                }}
                              >
                                #{t}
                              </span>
                            ))}
                            {p.tickets_sold.length > 4 && (
                              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                                +{p.tickets_sold.length - 4} more
                              </span>
                            )}
                          </div>
                        )}

                        {p.tickets_reserved.length > 0 && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flexWrap: 'wrap' }}>
                            <span style={{ fontSize: '0.72rem', color: 'var(--amber)', fontWeight: 600 }}>
                              Reserved ({p.tickets_reserved.length}):
                            </span>
                            {p.tickets_reserved.slice(0, 4).map((t) => (
                              <span
                                key={t}
                                style={{
                                  padding: '2px 6px',
                                  borderRadius: '4px',
                                  background: 'rgba(245, 158, 11, 0.15)',
                                  border: '1px solid rgba(245, 158, 11, 0.3)',
                                  fontFamily: 'monospace',
                                  fontSize: '0.75rem',
                                  fontWeight: 600,
                                  color: '#FBBF24',
                                }}
                              >
                                #{t}
                              </span>
                            ))}
                            {p.tickets_reserved.length > 4 && (
                              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                                +{p.tickets_reserved.length - 4} more
                              </span>
                            )}
                          </div>
                        )}

                        {p.tickets_sold.length === 0 && p.tickets_reserved.length === 0 && (
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            No active tickets
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Channel */}
                    <td>
                      {latestPayment ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          {isTelebirr && (
                            <span
                              style={{
                                padding: '4px 8px',
                                borderRadius: '6px',
                                background: 'rgba(6, 182, 212, 0.15)',
                                border: '1px solid rgba(6, 182, 212, 0.35)',
                                color: '#38BDF8',
                                fontSize: '0.75rem',
                                fontWeight: 700,
                                textTransform: 'uppercase',
                                letterSpacing: '0.04em',
                              }}
                            >
                              📱 Telebirr
                            </span>
                          )}
                          {isCBE && (
                            <span
                              style={{
                                padding: '4px 8px',
                                borderRadius: '6px',
                                background: 'rgba(168, 85, 247, 0.15)',
                                border: '1px solid rgba(168, 85, 247, 0.35)',
                                color: '#C084FC',
                                fontSize: '0.75rem',
                                fontWeight: 700,
                                textTransform: 'uppercase',
                                letterSpacing: '0.04em',
                              }}
                            >
                              🏦 CBE
                            </span>
                          )}
                          {!isTelebirr && !isCBE && (
                            <span
                              style={{
                                padding: '4px 8px',
                                borderRadius: '6px',
                                background: 'rgba(255, 255, 255, 0.08)',
                                border: '1px solid var(--border-subtle)',
                                color: '#FFF',
                                fontSize: '0.75rem',
                                fontWeight: 600,
                                textTransform: 'uppercase',
                              }}
                            >
                              {latestPayment.payment_method_display || latestPayment.payment_method}
                            </span>
                          )}
                        </div>
                      ) : (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>—</span>
                      )}
                    </td>

                    {/* Amount */}
                    <td>
                      {latestPayment ? (
                        <div style={{ fontWeight: 700, color: 'var(--emerald)' }}>
                          {latestPayment.amount} ETB
                        </div>
                      ) : (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>—</span>
                      )}
                    </td>

                    {/* Receipt Proof (Screenshot or PDF) Preview */}
                    <td>
                      {latestPayment?.payment_proof ? (
                        (() => {
                          const isPdf = (latestPayment.payment_proof || '').toLowerCase().endsWith('.pdf');
                          return isPdf ? (
                            <a
                              href={latestPayment.payment_proof}
                              target="_blank"
                              rel="noreferrer"
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '8px',
                                textDecoration: 'none',
                              }}
                              title="Click to open PDF receipt in new tab"
                            >
                              <div
                                style={{
                                  width: '42px',
                                  height: '42px',
                                  borderRadius: '6px',
                                  border: '1px solid rgba(239, 68, 68, 0.4)',
                                  background: 'rgba(239, 68, 68, 0.15)',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  color: '#F87171',
                                }}
                              >
                                <FileText size={20} />
                              </div>
                              <span
                                style={{
                                  fontSize: '0.75rem',
                                  color: '#F87171',
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: '3px',
                                  textDecoration: 'underline',
                                  fontWeight: 600,
                                }}
                              >
                                <ExternalLink size={13} />
                                <span>PDF Receipt</span>
                              </span>
                            </a>
                          ) : (
                            <div
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '8px',
                                cursor: 'pointer',
                              }}
                              onClick={() =>
                                setActiveLightboxImg({
                                  url: latestPayment.payment_proof!,
                                  title: `Receipt for ${p.full_name} (${latestPayment.payment_method_display})`,
                                })
                              }
                              title="Click to view full-size receipt screenshot"
                            >
                              <div
                                style={{
                                  width: '42px',
                                  height: '42px',
                                  borderRadius: '6px',
                                  overflow: 'hidden',
                                  border: '1px solid var(--border-prominent)',
                                  position: 'relative',
                                  background: '#000',
                                }}
                              >
                                <img
                                  src={latestPayment.payment_proof}
                                  alt="Receipt preview"
                                  style={{
                                    width: '100%',
                                    height: '100%',
                                    objectFit: 'cover',
                                    transition: 'transform 0.2s',
                                  }}
                                  onMouseOver={(e) => (e.currentTarget.style.transform = 'scale(1.15)')}
                                  onMouseOut={(e) => (e.currentTarget.style.transform = 'scale(1)')}
                                />
                              </div>
                              <span
                                style={{
                                  fontSize: '0.75rem',
                                  color: 'var(--cyan)',
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: '3px',
                                  textDecoration: 'underline',
                                }}
                              >
                                <Eye size={13} />
                                <span>View Proof</span>
                              </span>
                            </div>
                          );
                        })()
                      ) : (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          No proof
                        </span>
                      )}
                    </td>

                    {/* Reference Code */}
                    <td>
                      {latestPayment?.transaction_reference ? (
                        <code
                          style={{
                            fontFamily: 'monospace',
                            fontSize: '0.78rem',
                            fontWeight: 700,
                            color: 'var(--primary)',
                          }}
                        >
                          {latestPayment.transaction_reference}
                        </code>
                      ) : (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>—</span>
                      )}
                    </td>

                    {/* Action */}
                    <td style={{ textAlign: 'right' }}>
                      {latestPayment ? (
                        <button
                          type="button"
                          onClick={() => handleOpenInspection(latestPayment.id)}
                          className={`btn btn-sm ${
                            latestPayment.status === 'pending' ? 'btn-primary' : 'btn-secondary'
                          }`}
                          style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                        >
                          {latestPayment.status === 'pending' ? (
                            <>
                              <CheckCircle2 size={14} />
                              <span>Verify Payment</span>
                            </>
                          ) : (
                            <>
                              <Eye size={14} />
                              <span>Details</span>
                            </>
                          )}
                        </button>
                      ) : (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          No Payment
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Lightbox Modal for Receipt Screenshot Inspection */}
      {activeLightboxImg && (
        <div
          className="modal-backdrop"
          style={{ zIndex: 120, background: 'rgba(0, 0, 0, 0.88)' }}
          onClick={() => setActiveLightboxImg(null)}
        >
          <div
            style={{
              position: 'relative',
              maxWidth: '92vw',
              maxHeight: '92vh',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header bar on lightbox */}
            <div
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 16px',
                background: 'rgba(20, 20, 30, 0.95)',
                borderRadius: '8px 8px 0 0',
                border: '1px solid var(--border-subtle)',
                borderBottom: 'none',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ImageIcon size={18} color="var(--primary)" />
                <span style={{ fontWeight: 600, color: '#FFF', fontSize: '0.9rem' }}>
                  {activeLightboxImg.title}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <a
                  href={activeLightboxImg.url}
                  target="_blank"
                  rel="noreferrer"
                  className="btn btn-secondary btn-sm"
                  style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                >
                  <ExternalLink size={13} />
                  <span>Open in New Tab</span>
                </a>
                <button
                  type="button"
                  onClick={() => setActiveLightboxImg(null)}
                  className="btn btn-secondary btn-sm"
                  style={{ padding: '4px 8px' }}
                >
                  <X size={16} />
                </button>
              </div>
            </div>

            {/* Main image */}
            <div
              style={{
                background: '#0a0a0f',
                padding: '12px',
                borderRadius: '0 0 8px 8px',
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                overflow: 'auto',
                maxHeight: '80vh',
              }}
            >
              <img
                src={activeLightboxImg.url}
                alt="Receipt Full Preview"
                style={{
                  maxWidth: '100%',
                  maxHeight: '75vh',
                  objectFit: 'contain',
                  borderRadius: '4px',
                  boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Payment Inspection Modal */}
      <PaymentInspectionModal
        payment={selectedPayment}
        isOpen={!!selectedPayment}
        onClose={() => setSelectedPayment(null)}
        onActionComplete={() => {
          if (selectedLotteryId) {
            fetchParticipants(selectedLotteryId);
          }
        }}
      />
    </div>
  );
};
