import React, { useEffect, useState } from 'react';
import {
  Award,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Trophy,
} from 'lucide-react';
import { drawsApi } from '../api/draws';
import { lotteriesApi } from '../api/lotteries';
import { Draw, Lottery, Winner } from '../api/types';
import { useAuth } from '../context/AuthContext';

export const DrawExecution: React.FC = () => {
  const [closedLotteries, setClosedLotteries] = useState<Lottery[]>([]);
  const [selectedLotteryId, setSelectedLotteryId] = useState<string>('');
  const [pastDraws, setPastDraws] = useState<Draw[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDrawing, setIsDrawing] = useState(false);
  const [activeDrawResult, setActiveDrawResult] = useState<Draw | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Claim Prize State
  const [claimWinner, setClaimWinner] = useState<Winner | null>(null);
  const [payoutRef, setPayoutRef] = useState('');
  const [claimLoading, setClaimLoading] = useState(false);

  const { isDrawOfficer, isLotteryManager } = useAuth();

  const loadData = async () => {
    setLoading(true);
    try {
      const [lotteriesRes, drawsRes] = await Promise.all([
        lotteriesApi.getLotteries({ status: 'closed' }),
        drawsApi.getDraws(),
      ]);
      setClosedLotteries(lotteriesRes.results);
      if (lotteriesRes.results.length > 0 && !selectedLotteryId) {
        setSelectedLotteryId(lotteriesRes.results[0].id);
      }
      setPastDraws(drawsRes.results);
    } catch (err) {
      console.error('Error loading draw data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleExecuteDraw = async () => {
    if (!selectedLotteryId) return;
    setError(null);
    setIsDrawing(true);

    try {
      // Small artificial delay for suspense animation effect
      await new Promise((r) => setTimeout(r, 1200));

      const draw = await drawsApi.executeDraw(selectedLotteryId);
      setActiveDrawResult(draw);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to execute draw.');
    } finally {
      setIsDrawing(false);
    }
  };

  const handleClaimPrize = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!claimWinner || !payoutRef.trim()) return;

    setClaimLoading(true);
    try {
      await drawsApi.claimPrize(claimWinner.id, payoutRef);
      setClaimWinner(null);
      setPayoutRef('');
      loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to record prize claim.');
    } finally {
      setClaimLoading(false);
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="flex-between" style={{ marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', marginBottom: '4px' }}>Cryptographic Draw Engine</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Provably fair, cryptographically secure random winner determination using Python secrets CSPRNG.
          </p>
        </div>

        <button onClick={loadData} className="btn btn-secondary btn-sm">
          <RefreshCw size={16} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Draw Execution Terminal Card */}
      {isDrawOfficer && (
        <div className="card card-glass" style={{ marginBottom: '32px', position: 'relative', overflow: 'hidden' }}>
          <div style={{
            position: 'absolute',
            top: 0,
            right: 0,
            width: '300px',
            height: '100%',
            background: 'radial-gradient(circle at 100% 50%, rgba(99, 102, 241, 0.15) 0%, transparent 70%)',
            pointerEvents: 'none'
          }} />

          <div style={{ maxWidth: '650px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--gold)', marginBottom: '8px' }}>
              <Trophy size={20} />
              <span style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Live Draw Operations Center
              </span>
            </div>

            <h3 style={{ fontSize: '1.35rem', marginBottom: '10px' }}>Execute Official Lottery Draw</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: '20px' }}>
              Select a closed lottery to execute the tamper-proof cryptographic draw.
              Exactly 3 distinct winning tickets will be selected at random from verified sold tickets.
            </p>

            {error && (
              <div style={{
                padding: '12px',
                borderRadius: '8px',
                background: 'var(--rose-surface)',
                color: '#FCA5A5',
                fontSize: '0.85rem',
                marginBottom: '16px'
              }}>
                {error}
              </div>
            )}

            <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
              <div className="form-group" style={{ flex: 1, minWidth: '240px', marginBottom: 0 }}>
                <label className="form-label">Select Closed Lottery</label>
                <select
                  className="form-select"
                  value={selectedLotteryId}
                  onChange={(e) => setSelectedLotteryId(e.target.value)}
                  disabled={isDrawing}
                >
                  {closedLotteries.length === 0 ? (
                    <option value="">No closed lotteries ready for draw</option>
                  ) : (
                    closedLotteries.map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.name} ({l.sold_tickets_count || 0} tickets sold)
                      </option>
                    ))
                  )}
                </select>
              </div>

              <button
                type="button"
                disabled={isDrawing || !selectedLotteryId || closedLotteries.length === 0}
                onClick={handleExecuteDraw}
                className="btn btn-primary btn-lg"
                style={{
                  background: 'linear-gradient(135deg, var(--primary), #8B5CF6)',
                  boxShadow: '0 0 20px rgba(99, 102, 241, 0.4)',
                }}
              >
                <Sparkles size={20} className={isDrawing ? 'spin' : ''} />
                <span>{isDrawing ? 'Selecting Winning Numbers...' : 'Execute Official Draw'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Active Draw Results Showcase Banner */}
      {activeDrawResult && (
        <div className="card" style={{
          marginBottom: '32px',
          background: 'linear-gradient(145deg, rgba(22, 29, 46, 0.95), rgba(16, 22, 36, 0.98))',
          border: '1px solid rgba(245, 158, 11, 0.4)',
          boxShadow: '0 0 30px rgba(245, 158, 11, 0.15)'
        }}>
          <div className="flex-between" style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                background: 'rgba(245, 158, 11, 0.2)',
                color: 'var(--gold)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Trophy size={20} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.25rem', color: '#FFF' }}>
                  🎉 Official Draw Completed: {activeDrawResult.lottery.name}
                </h3>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  Drawn on {new Date(activeDrawResult.executed_at).toLocaleString()} by {activeDrawResult.executed_by.full_name}
                </span>
              </div>
            </div>

            <button onClick={() => setActiveDrawResult(null)} className="btn btn-secondary btn-sm">
              Dismiss
            </button>
          </div>

          {/* 3 Winning Podiums */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
            {activeDrawResult.winners.map((winner) => {
              const medal = winner.position === 1 ? '🥇 1st Prize' : winner.position === 2 ? '🥈 2nd Prize' : '🥉 3rd Prize';
              const borderCol = winner.position === 1 ? 'var(--gold)' : winner.position === 2 ? 'var(--silver)' : 'var(--bronze)';

              return (
                <div
                  key={winner.id}
                  style={{
                    padding: '20px',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-surface-elevated)',
                    border: `1px solid ${borderCol}`,
                    textAlign: 'center',
                  }}
                >
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: borderCol, marginBottom: '6px' }}>
                    {medal}
                  </div>
                  <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
                    {winner.prize_name}
                  </div>
                  {winner.prize_description && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic', marginTop: '2px' }}>
                      {winner.prize_description}
                    </div>
                  )}
                  <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#FFF', margin: '8px 0', fontFamily: 'monospace' }}>
                    #{winner.ticket?.ticket_number || (winner as any).ticket_number || '—'}
                  </div>
                  {Number(winner.prize_value) > 0 ? (
                    <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--emerald)' }}>
                      {Number(winner.prize_value).toLocaleString()} ETB
                    </div>
                  ) : (
                    <span className="badge badge-primary" style={{ fontSize: '0.75rem' }}>
                      🎁 Physical / Object Prize
                    </span>
                  )}
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginTop: '8px' }}>
                    Winner: <b>{winner.customer?.full_name || (winner as any).customer_name || 'Anonymous'}</b>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Cryptographic Entropy Proof */}
          <div style={{
            padding: '12px 16px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--bg-app)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.8rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldCheck size={16} color="var(--emerald)" />
              <span style={{ color: 'var(--text-secondary)' }}>SHA-256 Entropy Audit Proof:</span>
              <code style={{ color: 'var(--primary)', fontWeight: 600 }}>
                {activeDrawResult.randomness_hash}
              </code>
            </div>
            <span style={{ color: 'var(--text-muted)' }}>
              Eligible Pool: <b>{(activeDrawResult as any).sold_tickets_pool_count || (activeDrawResult as any).total_eligible_tickets || 0} verified sold tickets</b>
            </span>
          </div>
        </div>
      )}

      {/* Past Completed Draws & Winners Ledger */}
      <div className="card">
        <h3 style={{ fontSize: '1.15rem', marginBottom: '16px' }}>Past Completed Draws & Verified Winners</h3>

        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Lottery Event</th>
                <th>Draw Date</th>
                <th>Winning Ticket #</th>
                <th>Position & Prize</th>
                <th>Winner Identity</th>
                <th>Claim Status</th>
                <th style={{ textAlign: 'right' }}>Claim Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-secondary)' }}>
                    Loading draws...
                  </td>
                </tr>
              ) : pastDraws.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                    No draws executed yet.
                  </td>
                </tr>
              ) : (
                pastDraws.flatMap((draw) => {
                  const lotteryTitle = (draw as any).lottery?.name || (draw as any).lottery_name || 'Lottery';
                  const formattedDrawDate = draw.executed_at ? new Date(draw.executed_at).toLocaleDateString() : '—';

                  return (draw.winners || []).map((winner) => {
                    const ticketNum = winner.ticket?.ticket_number || (winner as any).ticket_number || '—';
                    const custName = winner.customer?.full_name || (winner as any).customer_name || 'Anonymous';
                    const custPhone = winner.customer?.phone_number || (winner as any).customer_phone || '';

                    return (
                      <tr key={winner.id}>
                        <td style={{ fontWeight: 600 }}>{lotteryTitle}</td>
                        <td style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                          {formattedDrawDate}
                        </td>
                        <td>
                          <code style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--primary)' }}>
                            #{ticketNum}
                          </code>
                        </td>
                        <td>
                          <div style={{ fontWeight: 600 }}>{winner.position_display}</div>
                          <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>{winner.prize_name}</div>
                          {winner.prize_description && (
                            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                              {winner.prize_description}
                            </div>
                          )}
                          {Number(winner.prize_value) > 0 ? (
                            <div style={{ fontSize: '0.8rem', color: 'var(--emerald)', marginTop: '2px' }}>
                              {Number(winner.prize_value).toLocaleString()} ETB
                            </div>
                          ) : (
                            <span style={{ fontSize: '0.72rem', color: 'var(--gold)', display: 'inline-block', marginTop: '2px' }}>
                              🎁 Physical Prize
                            </span>
                          )}
                        </td>
                        <td>
                          <div>{custName}</div>
                          {custPhone && (
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                              {custPhone}
                            </div>
                          )}
                        </td>
                        <td>
                          <span className={`badge ${winner.claim_status === 'claimed' ? 'badge-approved' : 'badge-pending'}`}>
                            {winner.claim_status}
                          </span>
                        </td>
                      <td style={{ textAlign: 'right' }}>
                        {winner.claim_status === 'unclaimed' && isLotteryManager ? (
                          <button
                            onClick={() => setClaimWinner(winner)}
                            className="btn btn-secondary btn-sm"
                          >
                            <Award size={14} color="var(--gold)" />
                            <span>Claim Prize</span>
                          </button>
                        ) : (
                          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            {winner.payout_reference ? `Ref: ${winner.payout_reference}` : '—'}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                });
              })
            )}</tbody>
          </table>
        </div>
      </div>

      {/* Claim Modal */}
      {claimWinner && (
        <div className="modal-backdrop" onClick={() => setClaimWinner(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 style={{ fontSize: '1.2rem' }}>Confirm Prize Handover</h3>
              <button onClick={() => setClaimWinner(null)} className="btn btn-secondary btn-sm">
                ✕
              </button>
            </div>

            <form onSubmit={handleClaimPrize}>
              <div className="modal-body">
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
                  Recording prize claim for <b>{claimWinner.customer?.full_name || (claimWinner as any).customer_name || 'Customer'}</b> ({claimWinner.position_display} — <b>{claimWinner.prize_name}</b>
                  {Number(claimWinner.prize_value) > 0 ? ` [${Number(claimWinner.prize_value).toLocaleString()} ETB]` : ''}
                  {claimWinner.prize_description ? ` • ${claimWinner.prize_description}` : ''}).
                </p>

                <div className="form-group">
                  <label className="form-label">Handover Voucher / Bank Payout / Serial / IMEI Reference *</label>
                  <input
                    type="text"
                    required
                    className="form-control"
                    placeholder="e.g. CBE-PAY-987654, CHEQUE#123, or Handover Voucher / Serial / IMEI #"
                    value={payoutRef}
                    onChange={(e) => setPayoutRef(e.target.value)}
                  />
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginTop: '4px' }}>
                    Enter the bank payout transaction ref, cheque number, or signed equipment/object handover receipt number.
                  </span>
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" onClick={() => setClaimWinner(null)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={claimLoading} className="btn btn-success">
                  {claimLoading ? 'Recording...' : 'Confirm Handover'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
