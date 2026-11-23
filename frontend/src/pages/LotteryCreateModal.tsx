import React, { useState } from 'react';
import { X } from 'lucide-react';
import { lotteriesApi } from '../api/lotteries';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export const LotteryCreateModal: React.FC<Props> = ({ isOpen, onClose, onCreated }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [ticketPrice, setTicketPrice] = useState('50.00');
  const [totalNumbers, setTotalNumbers] = useState(1000);
  const [startDate, setStartDate] = useState(new Date().toISOString().slice(0, 16));
  const [closingDate, setClosingDate] = useState(
    new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 16)
  );
  const [drawDate, setDrawDate] = useState(
    new Date(Date.now() + 8 * 86400000).toISOString().slice(0, 16)
  );

  // 1st Prize
  const [firstPrizeName, setFirstPrizeName] = useState('');
  const [firstPrizeDescription, setFirstPrizeDescription] = useState('');
  const [firstPrizeValue, setFirstPrizeValue] = useState('');

  // 2nd Prize
  const [secondPrizeName, setSecondPrizeName] = useState('');
  const [secondPrizeDescription, setSecondPrizeDescription] = useState('');
  const [secondPrizeValue, setSecondPrizeValue] = useState('');

  // 3rd Prize
  const [thirdPrizeName, setThirdPrizeName] = useState('');
  const [thirdPrizeDescription, setThirdPrizeDescription] = useState('');
  const [thirdPrizeValue, setThirdPrizeValue] = useState('');

  const [reservationHours, setReservationHours] = useState(48);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await lotteriesApi.createLottery({
        name,
        description,
        ticket_price: ticketPrice,
        total_numbers: Number(totalNumbers),
        start_date: new Date(startDate).toISOString(),
        closing_date: new Date(closingDate).toISOString(),
        draw_date: new Date(drawDate).toISOString(),
        first_prize_name: firstPrizeName,
        first_prize_description: firstPrizeDescription,
        first_prize_value: firstPrizeValue || '0',
        second_prize_name: secondPrizeName,
        second_prize_description: secondPrizeDescription,
        second_prize_value: secondPrizeValue || '0',
        third_prize_name: thirdPrizeName,
        third_prize_description: thirdPrizeDescription,
        third_prize_value: thirdPrizeValue || '0',
        reservation_hours: Number(reservationHours),
      });

      onCreated();
      onClose();
    } catch (err: any) {
      console.error(err);
      const msg = err.response?.data
        ? JSON.stringify(err.response.data)
        : 'Failed to create lottery. Please check field validations.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '750px' }}>
        <div className="modal-header">
          <div>
            <h3 style={{ fontSize: '1.25rem' }}>Create New Lottery</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Configure capacity, pricing, and prizes. Prizes can be money, objects (phone, car), or both.
            </p>
          </div>
          <button onClick={onClose} className="btn btn-secondary btn-sm" style={{ padding: '6px' }}>
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
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

            {/* General Info */}
            <div className="form-group">
              <label className="form-label">Lottery Event Name *</label>
              <input
                type="text"
                required
                className="form-control"
                placeholder="e.g. New Year Mega Jackpot Draw 2026"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Description / Promotion Details</label>
              <textarea
                className="form-control"
                rows={2}
                placeholder="Public details displayed on Telegram and portal..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            {/* Capacity & Price */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">Dynamic Ticket Capacity *</label>
                <input
                  type="number"
                  min={3}
                  max={500000}
                  required
                  className="form-control"
                  placeholder="e.g. 1000"
                  value={totalNumbers}
                  onChange={(e) => setTotalNumbers(Number(e.target.value))}
                />
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  Tickets (0000 to {totalNumbers - 1}) generated automatically.
                </span>
              </div>

              <div className="form-group">
                <label className="form-label">Ticket Price (ETB) *</label>
                <input
                  type="text"
                  required
                  className="form-control"
                  placeholder="50.00"
                  value={ticketPrice}
                  onChange={(e) => setTicketPrice(e.target.value)}
                />
              </div>
            </div>

            {/* Prize Hierarchy */}
            <div style={{
              margin: '20px 0',
              padding: '16px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-subtle)'
            }}>
              <div style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--gold)', marginBottom: '4px' }}>
                🏆 Three Winning Prize Positions
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '14px' }}>
                Each prize can be cash (ETB), an object (car, phone, etc.), or both. Leave "Estimated Value" empty for non-monetary prizes.
              </div>

              {/* 1st Prize */}
              <div style={{
                padding: '12px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--gold)',
                background: 'rgba(245, 158, 11, 0.05)',
                marginBottom: '10px'
              }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--gold)', marginBottom: '8px' }}>🥇 1st Prize</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '8px' }}>
                  <div>
                    <label className="form-label">Prize Title *</label>
                    <input
                      type="text"
                      required
                      className="form-control"
                      placeholder='e.g. "Toyota Corolla" or "500,000 ETB Cash"'
                      value={firstPrizeName}
                      onChange={(e) => setFirstPrizeName(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="form-label">Estimated Value (ETB)</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="0 for non-cash prizes"
                      value={firstPrizeValue}
                      onChange={(e) => setFirstPrizeValue(e.target.value)}
                    />
                  </div>
                </div>
                <div>
                  <label className="form-label">Description</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. Brand new 2026 model, red, or Cash prize"
                    value={firstPrizeDescription}
                    onChange={(e) => setFirstPrizeDescription(e.target.value)}
                  />
                </div>
              </div>

              {/* 2nd Prize */}
              <div style={{
                padding: '12px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--silver, #94a3b8)',
                background: 'rgba(148, 163, 184, 0.05)',
                marginBottom: '10px'
              }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--silver, #94a3b8)', marginBottom: '8px' }}>🥈 2nd Prize</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '8px' }}>
                  <div>
                    <label className="form-label">Prize Title *</label>
                    <input
                      type="text"
                      required
                      className="form-control"
                      placeholder="e.g. iPhone 16 Pro or 250,000 ETB"
                      value={secondPrizeName}
                      onChange={(e) => setSecondPrizeName(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="form-label">Estimated Value (ETB)</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="0 for non-cash prizes"
                      value={secondPrizeValue}
                      onChange={(e) => setSecondPrizeValue(e.target.value)}
                    />
                  </div>
                </div>
                <div>
                  <label className="form-label">Description</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. 256GB, Natural Titanium color"
                    value={secondPrizeDescription}
                    onChange={(e) => setSecondPrizeDescription(e.target.value)}
                  />
                </div>
              </div>

              {/* 3rd Prize */}
              <div style={{
                padding: '12px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--bronze, #cd7f32)',
                background: 'rgba(205, 127, 50, 0.05)',
              }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--bronze, #cd7f32)', marginBottom: '8px' }}>🥉 3rd Prize</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '8px' }}>
                  <div>
                    <label className="form-label">Prize Title *</label>
                    <input
                      type="text"
                      required
                      className="form-control"
                      placeholder="e.g. Samsung 55 Smart TV or 100,000 ETB"
                      value={thirdPrizeName}
                      onChange={(e) => setThirdPrizeName(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="form-label">Estimated Value (ETB)</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="0 for non-cash prizes"
                      value={thirdPrizeValue}
                      onChange={(e) => setThirdPrizeValue(e.target.value)}
                    />
                  </div>
                </div>
                <div>
                  <label className="form-label">Description</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder='e.g. "Smart TV with wall mount bracket"'
                    value={thirdPrizeDescription}
                    onChange={(e) => setThirdPrizeDescription(e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* Dates */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Start Sales Date</label>
                <input
                  type="datetime-local"
                  required
                  className="form-control"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Closing Deadline</label>
                <input
                  type="datetime-local"
                  required
                  className="form-control"
                  value={closingDate}
                  onChange={(e) => setClosingDate(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Live Draw Date</label>
                <input
                  type="datetime-local"
                  required
                  className="form-control"
                  value={drawDate}
                  onChange={(e) => setDrawDate(e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Reservation Expiration Window (Hours)</label>
              <input
                type="number"
                min={1}
                max={168}
                required
                className="form-control"
                value={reservationHours}
                onChange={(e) => setReservationHours(Number(e.target.value))}
              />
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Tickets are released if payment reference is not submitted within this window.
              </span>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="btn btn-primary">
              {loading ? 'Creating & Generating Tickets...' : 'Create Lottery'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
