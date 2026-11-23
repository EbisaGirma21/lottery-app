import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  FileText,
  Phone,
  Ticket,
  User,
  X,
  XCircle,
} from 'lucide-react';
import { paymentsApi } from '../api/payments';
import { Payment } from '../api/types';

interface Props {
  payment: Payment | null;
  isOpen: boolean;
  onClose: () => void;
  onActionComplete: () => void;
}

export const PaymentInspectionModal: React.FC<Props> = ({
  payment,
  isOpen,
  onClose,
  onActionComplete,
}) => {
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [verifyMessage, setVerifyMessage] = useState<string | null>(null);
  const [adminNotes, setAdminNotes] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');
  const [isRejectMode, setIsRejectMode] = useState(false);
  const [imageZoom, setImageZoom] = useState(false);

  if (!isOpen || !payment) return null;

  const isPending = payment.status === 'pending';

  const handleVerifyNow = async () => {
    setError(null);
    setVerifyMessage(null);
    setVerifying(true);
    try {
      const updated = await paymentsApi.verifyPaymentNow(payment.id);
      if (updated.is_auto_verified && updated.status === 'approved') {
        setVerifyMessage('⚡ Successfully confirmed against official bank ledger! Payment marked Approved.');
        setTimeout(() => {
          onActionComplete();
          onClose();
        }, 1200);
      } else {
        setVerifyMessage(
          `Bank API Result (${updated.auto_verification_status || 'PENDING'}): ${
            updated.verification_error || 'Not confirmed by bank records yet.'
          }`
        );
        onActionComplete();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to query bank verification API.');
    } finally {
      setVerifying(false);
    }
  };

  const handleApprove = async () => {
    setError(null);
    setLoading(true);
    try {
      await paymentsApi.approvePayment(payment.id, adminNotes);
      onActionComplete();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to approve payment.');
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    if (!rejectionReason.trim()) {
      setError('A rejection reason is required to inform the customer.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await paymentsApi.rejectPayment(payment.id, rejectionReason);
      onActionComplete();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reject payment.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '800px', display: 'flex', flexDirection: 'column' }}
      >
        {/* Header */}
        <div className="modal-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3 style={{ fontSize: '1.25rem' }}>Verify Payment Proof</h3>
              <span className={`badge badge-${payment.status}`}>
                {payment.status}
              </span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
              Verify transaction reference against bank statements before confirming ticket sale.
            </p>
          </div>
          <button onClick={onClose} className="btn btn-secondary btn-sm" style={{ padding: '6px' }}>
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="modal-body" style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '24px' }}>
          {/* Left Column: Transaction Details & Customer */}
          <div>
            {error && (
              <div style={{
                padding: '10px 14px',
                borderRadius: '8px',
                background: 'var(--rose-surface)',
                color: '#FCA5A5',
                fontSize: '0.85rem',
                marginBottom: '16px',
                border: '1px solid rgba(239, 68, 68, 0.3)'
              }}>
                {error}
              </div>
            )}

            {/* Financial Details */}
            <div style={{
              padding: '16px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-subtle)',
              marginBottom: '16px'
            }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
                Bank Transaction Reference
              </div>
              <div style={{ fontSize: '1.35rem', fontWeight: 800, fontFamily: 'monospace', color: 'var(--primary)', letterSpacing: '0.05em' }}>
                {payment.transaction_reference}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '14px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>AMOUNT PAID</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--emerald)' }}>
                    {payment.amount} ETB
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>PAYMENT METHOD</div>
                  <div style={{ marginTop: '2px' }}>
                    {payment.payment_method.toLowerCase().includes('telebirr') ? (
                      <span
                        style={{
                          padding: '4px 8px',
                          borderRadius: '6px',
                          background: 'rgba(6, 182, 212, 0.2)',
                          border: '1px solid rgba(6, 182, 212, 0.4)',
                          color: '#38BDF8',
                          fontSize: '0.85rem',
                          fontWeight: 700,
                          display: 'inline-block',
                        }}
                      >
                        📱 Telebirr
                      </span>
                    ) : payment.payment_method.toLowerCase().includes('cbe') ? (
                      <span
                        style={{
                          padding: '4px 8px',
                          borderRadius: '6px',
                          background: 'rgba(168, 85, 247, 0.2)',
                          border: '1px solid rgba(168, 85, 247, 0.4)',
                          color: '#C084FC',
                          fontSize: '0.85rem',
                          fontWeight: 700,
                          display: 'inline-block',
                        }}
                      >
                        🏦 CBE Bank
                      </span>
                    ) : (
                      <span
                        style={{
                          padding: '4px 8px',
                          borderRadius: '6px',
                          background: 'rgba(255, 255, 255, 0.1)',
                          border: '1px solid var(--border-subtle)',
                          color: '#FFF',
                          fontSize: '0.85rem',
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          display: 'inline-block',
                        }}
                      >
                        {payment.payment_method}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {verifyMessage && (
              <div
                style={{
                  padding: '10px 14px',
                  borderRadius: '8px',
                  background: verifyMessage.includes('Successfully')
                    ? 'rgba(16, 185, 129, 0.15)'
                    : 'rgba(245, 158, 11, 0.15)',
                  color: verifyMessage.includes('Successfully') ? '#34D399' : '#FBBF24',
                  fontSize: '0.85rem',
                  marginBottom: '16px',
                  border: `1px solid ${
                    verifyMessage.includes('Successfully')
                      ? 'rgba(16, 185, 129, 0.35)'
                      : 'rgba(245, 158, 11, 0.35)'
                  }`,
                }}
              >
                {verifyMessage}
              </div>
            )}

            {/* Bank Ledger Verification Status */}
            <div
              style={{
                padding: '14px 16px',
                borderRadius: 'var(--radius-md)',
                background: payment.is_auto_verified
                  ? 'rgba(16, 185, 129, 0.08)'
                  : payment.auto_verification_status === 'FAILED'
                  ? 'rgba(239, 68, 68, 0.08)'
                  : 'var(--bg-surface-elevated)',
                border: `1px solid ${
                  payment.is_auto_verified
                    ? 'rgba(16, 185, 129, 0.3)'
                    : payment.auto_verification_status === 'FAILED'
                    ? 'rgba(239, 68, 68, 0.3)'
                    : 'var(--border-subtle)'
                }`,
                marginBottom: '16px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Bank Ledger Verification (Verify.ET / Check.et)
                </div>
                {payment.is_auto_verified ? (
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#10B981' }}>
                    ⚡ AUTO-CONFIRMED
                  </span>
                ) : (
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                    {payment.auto_verification_status || 'NOT YET VERIFIED'}
                  </span>
                )}
              </div>

              {payment.is_auto_verified ? (
                <div style={{ fontSize: '0.82rem', color: '#D1FAE5', lineHeight: 1.4 }}>
                  ✅ This transaction was verified directly against the official financial ledger. Receipt code, amount, and recipient matched.
                </div>
              ) : payment.verification_error ? (
                <div style={{ fontSize: '0.82rem', color: '#FCA5A5', lineHeight: 1.4 }}>
                  ⚠️ {payment.verification_error}
                </div>
              ) : (
                <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                  Click below to query official bank & wallet records in real time to verify this payment automatically.
                </div>
              )}
            </div>

            {/* Customer Information */}
            <div style={{
              padding: '14px 16px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-subtle)',
              marginBottom: '16px'
            }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
                Customer Account
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <User size={16} color="var(--primary)" />
                <span style={{ fontWeight: 600, color: '#FFF' }}>
                  {payment.customer?.full_name || (payment as any).customer_name || 'Anonymous Customer'}
                </span>
                {(payment.customer?.telegram_username || (payment as any).customer_telegram) && (
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    (@{payment.customer?.telegram_username || (payment as any).customer_telegram})
                  </span>
                )}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                <Phone size={14} />
                <span>
                  {payment.customer?.phone_number || (payment as any).customer_phone || 'No phone number registered'}
                </span>
              </div>
            </div>

            {/* Reserved / Covered Tickets */}
            <div>
              {(() => {
                const tickets: string[] = [];
                if (Array.isArray(payment.reservations)) {
                  payment.reservations.forEach((r: any) => {
                    const num = r.ticket_number || r.ticket?.ticket_number || (typeof r === 'string' ? r : null);
                    if (num) tickets.push(String(num));
                  });
                }
                if (tickets.length === 0 && Array.isArray((payment as any).ticket_numbers)) {
                  (payment as any).ticket_numbers.forEach((num: any) => {
                    if (num) tickets.push(String(num));
                  });
                }
                return (
                  <>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
                      Covered Tickets ({tickets.length})
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                      {tickets.length > 0 ? (
                        tickets.map((tNum, idx) => (
                          <span
                            key={idx}
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                              padding: '4px 8px',
                              borderRadius: '4px',
                              background: 'var(--bg-surface-elevated)',
                              border: '1px solid var(--border-prominent)',
                              fontSize: '0.82rem',
                              fontFamily: 'monospace',
                              fontWeight: 600,
                              color: '#FFF',
                            }}
                          >
                            <Ticket size={12} color="var(--primary)" />
                            #{tNum}
                          </span>
                        ))
                      ) : (
                        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                          No tickets listed
                        </span>
                      )}
                    </div>
                  </>
                );
              })()}
            </div>
          </div>

          {/* Right Column: Receipt Image Inspection */}
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
              Receipt Screenshot Proof
            </div>

            <div style={{
              flex: 1,
              minHeight: '220px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-app)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              overflow: 'hidden',
              position: 'relative'
            }}>
              {payment.payment_proof ? (
                (() => {
                  const isPdf = (payment.payment_proof || '').toLowerCase().endsWith('.pdf');
                  return isPdf ? (
                    <div style={{ textAlign: 'center', padding: '24px', width: '100%' }}>
                      <div style={{
                        width: '56px',
                        height: '56px',
                        borderRadius: '12px',
                        background: 'rgba(239, 68, 68, 0.15)',
                        border: '1px solid rgba(239, 68, 68, 0.4)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        margin: '0 auto 10px',
                        color: '#F87171',
                      }}>
                        <FileText size={30} />
                      </div>
                      <div style={{ fontWeight: 700, color: '#FFF', fontSize: '0.95rem', marginBottom: '4px' }}>
                        PDF Receipt Document Attached
                      </div>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '14px' }}>
                        Customer uploaded an electronic PDF transfer receipt.
                      </p>
                      <a
                        href={payment.payment_proof}
                        target="_blank"
                        rel="noreferrer"
                        className="btn btn-primary btn-sm"
                        style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                      >
                        <ExternalLink size={14} />
                        <span>Open PDF in New Window</span>
                      </a>
                    </div>
                  ) : (
                    <>
                      <img
                        src={payment.payment_proof}
                        alt="Payment receipt proof"
                        style={{
                          maxWidth: '100%',
                          maxHeight: '260px',
                          objectFit: 'contain',
                          cursor: 'zoom-in',
                        }}
                        onClick={() => setImageZoom(true)}
                      />
                      <button
                        type="button"
                        onClick={() => setImageZoom(true)}
                        className="btn btn-secondary btn-sm"
                        style={{
                          position: 'absolute',
                          bottom: '8px',
                          right: '8px',
                          background: 'rgba(0, 0, 0, 0.75)',
                          backdropFilter: 'blur(4px)',
                          padding: '4px 8px'
                        }}
                      >
                        <ExternalLink size={14} />
                        <span>Zoom</span>
                      </button>
                    </>
                  );
                })()
              ) : (
                <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>
                  <AlertTriangle size={32} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
                  <p style={{ fontSize: '0.85rem' }}>No receipt image uploaded.</p>
                  <p style={{ fontSize: '0.75rem' }}>Verify using reference on bank terminal.</p>
                </div>
              )}
            </div>

            {/* Verification Form (Only for pending) */}
            {isPending && (
              <div style={{ marginTop: '16px' }}>
                {!isRejectMode ? (
                  <div className="form-group">
                    <label className="form-label">Staff Verification Remarks (Optional)</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="e.g. Confirmed on CBE mobile banking ledger"
                      value={adminNotes}
                      onChange={(e) => setAdminNotes(e.target.value)}
                    />
                  </div>
                ) : (
                  <div className="form-group">
                    <label className="form-label" style={{ color: 'var(--rose)' }}>
                      Rejection Reason (Dispatched to customer) *
                    </label>
                    <textarea
                      required
                      className="form-control"
                      rows={2}
                      placeholder="e.g. Transaction reference not found on bank statement"
                      value={rejectionReason}
                      onChange={(e) => setRejectionReason(e.target.value)}
                      style={{ borderColor: 'var(--rose)' }}
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="modal-footer">
          <button type="button" onClick={onClose} className="btn btn-secondary">
            Close
          </button>

          {isPending && (
            <>
              {!isRejectMode ? (
                <>
                  <button
                    type="button"
                    disabled={loading || verifying}
                    onClick={handleVerifyNow}
                    className="btn btn-outline"
                    style={{
                      color: '#38BDF8',
                      borderColor: 'rgba(56, 189, 248, 0.4)',
                      background: 'rgba(6, 182, 212, 0.08)',
                    }}
                    title="Query official bank/wallet ledger via REST API"
                  >
                    <span>{verifying ? 'Checking Bank API...' : '⚡ Check Bank API'}</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsRejectMode(true)}
                    className="btn btn-outline"
                    style={{ color: 'var(--rose)', borderColor: 'rgba(239, 68, 68, 0.3)' }}
                  >
                    <XCircle size={16} />
                    <span>Reject Payment</span>
                  </button>
                  <button
                    type="button"
                    disabled={loading || verifying}
                    onClick={handleApprove}
                    className="btn btn-success"
                  >
                    <CheckCircle2 size={16} />
                    <span>{loading ? 'Confirming...' : 'Approve & Issue Tickets'}</span>
                  </button>
                </>
              ) : (
                <>
                  <button
                    type="button"
                    onClick={() => setIsRejectMode(false)}
                    className="btn btn-secondary"
                  >
                    Back to Approve
                  </button>
                  <button
                    type="button"
                    disabled={loading || !rejectionReason.trim()}
                    onClick={handleReject}
                    className="btn btn-danger"
                  >
                    <XCircle size={16} />
                    <span>{loading ? 'Rejecting...' : 'Confirm Rejection'}</span>
                  </button>
                </>
              )}
            </>
          )}
        </div>
      </div>

      {/* Full Size Image Modal Zoom */}
      {imageZoom && payment.payment_proof && (
        <div
          className="modal-backdrop"
          style={{ zIndex: 120, background: 'rgba(0, 0, 0, 0.92)' }}
          onClick={() => setImageZoom(false)}
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
                <span style={{ fontWeight: 600, color: '#FFF', fontSize: '0.9rem' }}>
                  Receipt Proof — {payment.customer.full_name} ({payment.payment_method.toUpperCase()})
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <a
                  href={payment.payment_proof}
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
                  onClick={() => setImageZoom(false)}
                  className="btn btn-secondary btn-sm"
                  style={{ padding: '4px 8px' }}
                >
                  <X size={16} />
                </button>
              </div>
            </div>

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
                src={payment.payment_proof}
                alt="Zoomed receipt"
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
    </div>
  );
};
