import React, { useEffect, useState } from 'react';
import { Eye, RefreshCw, Search, ShieldAlert, X } from 'lucide-react';
import { auditApi } from '../api/audit';
import { AuditLog } from '../api/types';

export const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params: Record<string, any> = {};
      if (search) params.search = search;
      const res = await auditApi.getAuditLogs(params);
      setLogs(res.results);
    } catch (err) {
      console.error('Error fetching audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchLogs();
  };

  return (
    <div>
      {/* Header */}
      <div className="flex-between" style={{ marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', marginBottom: '4px' }}>Immutable Audit Trail</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Permanent system records tracking every administrative change, draw execution, and payment decision.
          </p>
        </div>

        <button onClick={fetchLogs} className="btn btn-secondary btn-sm">
          <RefreshCw size={16} />
          <span>Refresh Logs</span>
        </button>
      </div>

      {/* Search Toolbar */}
      <div className="card" style={{ padding: '16px 20px', marginBottom: '24px' }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '12px', maxWidth: '450px' }}>
          <div className="input-icon-wrapper" style={{ flex: 1 }}>
            <Search className="input-icon" size={16} />
            <input
              type="text"
              className="form-control input-with-icon"
              placeholder="Search by action, actor, or entity..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <button type="submit" className="btn btn-secondary">
            Search
          </button>
        </form>
      </div>

      {/* Audit Logs Table */}
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Action Event</th>
              <th>Entity</th>
              <th>Actor</th>
              <th>IP Address</th>
              <th style={{ textAlign: 'right' }}>Payload</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-secondary)' }}>
                  Loading audit trail...
                </td>
              </tr>
            ) : logs.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                  No audit logs recorded yet.
                </td>
              </tr>
            ) : (
              logs.map((log) => (
                <tr key={log.id}>
                  <td style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td>
                    <code style={{ fontWeight: 700, color: 'var(--primary)', fontSize: '0.82rem' }}>
                      {log.action}
                    </code>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.85rem' }}>{log.entity_type}</span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block' }}>
                      ID: {log.entity_id ? `${log.entity_id.slice(0, 8)}...` : '—'}
                    </span>
                  </td>
                  <td>
                    <div style={{ fontSize: '0.85rem' }}>{log.actor_email || 'System Worker'}</div>
                    {log.actor_name && (
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{log.actor_name}</div>
                    )}
                  </td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {log.ip_address || 'Internal'}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      onClick={() => setSelectedLog(log)}
                      className="btn btn-secondary btn-sm"
                      title="Inspect payload"
                    >
                      <Eye size={14} />
                      <span>Diff</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Payload Modal */}
      {selectedLog && (
        <div className="modal-backdrop" onClick={() => setSelectedLog(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldAlert size={18} color="var(--primary)" />
                <h3 style={{ fontSize: '1.15rem' }}>Audit Event Payload</h3>
              </div>
              <button onClick={() => setSelectedLog(null)} className="btn btn-secondary btn-sm">
                <X size={16} />
              </button>
            </div>

            <div className="modal-body">
              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Action / Entity
                </div>
                <div style={{ fontWeight: 700, color: '#FFF' }}>
                  {selectedLog.action} on {selectedLog.entity_type} ({selectedLog.entity_id})
                </div>
              </div>

              {selectedLog.old_value && (
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--rose)', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Previous State (old_value)
                  </div>
                  <pre style={{
                    padding: '12px',
                    borderRadius: '8px',
                    background: 'var(--bg-app)',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '0.78rem',
                    color: '#F87171',
                    overflowX: 'auto',
                    fontFamily: 'monospace'
                  }}>
                    {JSON.stringify(selectedLog.old_value, null, 2)}
                  </pre>
                </div>
              )}

              {selectedLog.new_value && (
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--emerald)', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Updated State (new_value)
                  </div>
                  <pre style={{
                    padding: '12px',
                    borderRadius: '8px',
                    background: 'var(--bg-app)',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '0.78rem',
                    color: '#34D399',
                    overflowX: 'auto',
                    fontFamily: 'monospace'
                  }}>
                    {JSON.stringify(selectedLog.new_value, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button onClick={() => setSelectedLog(null)} className="btn btn-secondary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
