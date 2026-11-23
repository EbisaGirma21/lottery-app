import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  CheckCircle,
  Pause,
  Play,
  Plus,
  RefreshCw,
  Search,
  StopCircle,
  Ticket,
  Users,
} from 'lucide-react';
import { lotteriesApi } from '../api/lotteries';
import { Lottery, LotteryStatus } from '../api/types';
import { useAuth } from '../context/AuthContext';
import { LotteryCreateModal } from './LotteryCreateModal';

export const Lotteries: React.FC = () => {
  const [lotteries, setLotteries] = useState<Lottery[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const { isLotteryManager } = useAuth();

  const fetchLotteries = async () => {
    setLoading(true);
    try {
      const params: Record<string, any> = {};
      if (statusFilter !== 'all') params.status = statusFilter;
      if (searchQuery) params.search = searchQuery;

      const res = await lotteriesApi.getLotteries(params);
      setLotteries(res.results);
    } catch (err) {
      console.error('Error fetching lotteries:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLotteries();
  }, [statusFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchLotteries();
  };

  const handleStatusTransition = async (lottery: Lottery, newStatus: LotteryStatus) => {
    const confirmMsg = `Are you sure you want to transition "${lottery.name}" to ${newStatus.toUpperCase()}?`;
    if (!window.confirm(confirmMsg)) return;

    try {
      await lotteriesApi.changeStatus(lottery.id, newStatus);
      fetchLotteries();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to change lottery status.');
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="flex-between" style={{ marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', marginBottom: '4px' }}>Lottery Management</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Configure dynamic capacity, ticket pricing, and control lifecycle states.
          </p>
        </div>

        {isLotteryManager && (
          <button onClick={() => setIsCreateOpen(true)} className="btn btn-primary">
            <Plus size={18} />
            <span>Create Lottery</span>
          </button>
        )}
      </div>

      {/* Filters & Search Toolbar */}
      <div className="card" style={{ padding: '16px 20px', marginBottom: '24px' }}>
        <div className="flex-between" style={{ flexWrap: 'wrap', gap: '16px' }}>
          {/* Status Filter Tabs */}
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {['all', 'draft', 'open', 'paused', 'closed', 'drawn'].map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`btn btn-sm ${statusFilter === status ? 'btn-primary' : 'btn-secondary'}`}
                style={{ textTransform: 'capitalize' }}
              >
                {status}
              </button>
            ))}
          </div>

          {/* Search input */}
          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '8px' }}>
            <div className="input-icon-wrapper" style={{ width: '260px' }}>
              <Search className="input-icon" size={16} />
              <input
                type="text"
                className="form-control input-with-icon"
                style={{ padding: '8px 12px 8px 36px', fontSize: '0.85rem' }}
                placeholder="Search by lottery name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <button type="submit" className="btn btn-secondary btn-sm">
              Search
            </button>
          </form>
        </div>
      </div>

      {/* Lotteries Table */}
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Lottery Event</th>
              <th>Price</th>
              <th>Capacity</th>
              <th>Tickets Sold</th>
              <th>Draw Date</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
                  <RefreshCw size={24} className="spin" style={{ margin: '0 auto 8px' }} />
                  <div>Loading lotteries...</div>
                </td>
              </tr>
            ) : lotteries.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  No lotteries found matching criteria.
                </td>
              </tr>
            ) : (
              lotteries.map((l) => {
                const sold = l.sold_tickets_count || 0;
                const total = l.total_numbers;
                const pct = total > 0 ? Math.round((sold / total) * 100) : 0;

                return (
                  <tr key={l.id}>
                    <td>
                      <div style={{ fontWeight: 600, color: '#FFF', fontSize: '0.95rem' }}>{l.name}</div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        {l.description ? (l.description.length > 50 ? `${l.description.slice(0, 50)}...` : l.description) : 'No description'}
                      </div>
                    </td>
                    <td style={{ fontWeight: 600 }}>{l.ticket_price} ETB</td>
                    <td>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Ticket size={14} color="var(--primary)" />
                        <b>{l.total_numbers.toLocaleString()}</b>
                      </span>
                    </td>
                    <td>
                      <div>
                        <b>{sold.toLocaleString()}</b> ({pct}%)
                      </div>
                      <div style={{ width: '80px', height: '4px', background: 'var(--bg-surface-elevated)', borderRadius: '2px', marginTop: '4px' }}>
                        <div style={{ width: `${pct}%`, height: '100%', background: 'var(--emerald)', borderRadius: '2px' }} />
                      </div>
                    </td>
                    <td style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                      {new Date(l.draw_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                    </td>
                    <td>
                      <span className={`badge badge-${l.status}`}>
                        {l.status}
                      </span>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '6px' }}>
                        <Link
                          to={`/participants?lottery=${l.id}`}
                          className="btn btn-secondary btn-sm"
                          title="View Applicants & Payment Proofs"
                        >
                          <Users size={14} />
                          <span>Applicants</span>
                        </Link>

                        {l.status === 'draft' && isLotteryManager && (
                          <button
                            onClick={() => handleStatusTransition(l, 'open')}
                            className="btn btn-success btn-sm"
                            title="Open ticket sales"
                          >
                            <Play size={14} />
                            <span>Open</span>
                          </button>
                        )}

                        {l.status === 'open' && isLotteryManager && (
                          <>
                            <button
                              onClick={() => handleStatusTransition(l, 'paused')}
                              className="btn btn-secondary btn-sm"
                              title="Pause sales temporarily"
                            >
                              <Pause size={14} />
                              <span>Pause</span>
                            </button>
                            <button
                              onClick={() => handleStatusTransition(l, 'closed')}
                              className="btn btn-danger btn-sm"
                              title="Close sales before draw"
                            >
                              <StopCircle size={14} />
                              <span>Close</span>
                            </button>
                          </>
                        )}

                        {l.status === 'paused' && isLotteryManager && (
                          <button
                            onClick={() => handleStatusTransition(l, 'open')}
                            className="btn btn-success btn-sm"
                            title="Resume sales"
                          >
                            <Play size={14} />
                            <span>Resume</span>
                          </button>
                        )}

                        {l.status === 'drawn' && (
                          <span style={{ fontSize: '0.78rem', color: 'var(--gold)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                            <CheckCircle size={14} />
                            <span>Drawn</span>
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      <LotteryCreateModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onCreated={fetchLotteries}
      />
    </div>
  );
};
