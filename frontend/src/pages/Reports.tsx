import React, { useEffect, useState } from 'react';
import {
  Download,
  FileSpreadsheet,
  FileText,
  RefreshCw,
  TrendingUp,
} from 'lucide-react';
import { lotteriesApi } from '../api/lotteries';
import { reportsApi } from '../api/reports';
import { DashboardAnalytics, Lottery } from '../api/types';

export const Reports: React.FC = () => {
  const [data, setData] = useState<DashboardAnalytics | null>(null);
  const [lotteries, setLotteries] = useState<Lottery[]>([]);
  const [selectedLotteryId, setSelectedLotteryId] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState<string | null>(null);

  const loadReports = async () => {
    setLoading(true);
    try {
      const [analytics, lotteriesRes] = await Promise.all([
        reportsApi.getDashboardAnalytics(),
        lotteriesApi.getLotteries(),
      ]);
      setData(analytics);
      setLotteries(lotteriesRes.results);
      if (lotteriesRes.results.length > 0) {
        setSelectedLotteryId(lotteriesRes.results[0].id);
      }
    } catch (err) {
      console.error('Error loading report analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const handleDownloadFinancialExcel = async () => {
    setDownloading('financial');
    try {
      await reportsApi.downloadFinancialExcel();
    } catch (err) {
      alert('Failed to download financial report.');
    } finally {
      setDownloading(null);
    }
  };

  const handleDownloadLotterySalesExcel = async () => {
    if (!selectedLotteryId) return;
    setDownloading('lottery-sales');
    try {
      await reportsApi.downloadLotterySalesExcel(selectedLotteryId);
    } catch (err) {
      alert('Failed to download lottery sales report.');
    } finally {
      setDownloading(null);
    }
  };

  const handleDownloadLotteryPdf = async () => {
    if (!selectedLotteryId) return;
    setDownloading('lottery-pdf');
    try {
      await reportsApi.downloadLotterySummaryPdf(selectedLotteryId);
    } catch (err) {
      alert('Failed to download PDF summary report.');
    } finally {
      setDownloading(null);
    }
  };

  if (loading && !data) {
    return (
      <div style={{ padding: '60px 0', textAlign: 'center', color: 'var(--text-secondary)' }}>
        <RefreshCw size={32} className="spin" style={{ margin: '0 auto 16px' }} />
        <p>Loading analytics reports...</p>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex-between" style={{ marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', marginBottom: '4px' }}>Executive Reports & Analytics</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Generate and export financial reconciliation spreadsheets and executive summary PDFs.
          </p>
        </div>

        <button onClick={loadReports} className="btn btn-secondary btn-sm">
          <RefreshCw size={16} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Analytics Summary */}
      <div className="stat-grid" style={{ marginBottom: '32px' }}>
        <div className="stat-card" style={{ '--stat-accent': 'var(--emerald)' } as React.CSSProperties}>
          <div>
            <div className="stat-label">Total Verified Revenue</div>
            <div className="stat-value" style={{ color: 'var(--emerald)' }}>
              {Number(data?.total_revenue || 0).toLocaleString()} <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>ETB</span>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '8px' }}>
              Monthly: <b>{Number(data?.monthly_revenue || 0).toLocaleString()} ETB</b>
            </div>
          </div>
          <TrendingUp size={28} color="var(--emerald)" />
        </div>

        <div className="stat-card" style={{ '--stat-accent': 'var(--primary)' } as React.CSSProperties}>
          <div>
            <div className="stat-label">Total Tickets Sold</div>
            <div className="stat-value" style={{ color: 'var(--primary)' }}>
              {data?.total_tickets_sold?.toLocaleString() || 0}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '8px' }}>
              Conversion: <b>{data?.overall_conversion_rate || 0}%</b>
            </div>
          </div>
          <FileSpreadsheet size={28} color="var(--primary)" />
        </div>
      </div>

      {/* Export Hub Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '24px' }}>
        {/* 1. Financial Revenue Excel */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '14px' }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              background: 'var(--emerald-surface)',
              color: 'var(--emerald)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <FileSpreadsheet size={22} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.15rem' }}>Financial Revenue Breakdown</h3>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Spreadsheet (.xlsx)</span>
            </div>
          </div>

          <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: '20px', lineHeight: 1.5 }}>
            Export comprehensive verified revenue breakdowns aggregated by payment channel
            (Telebirr, Commercial Bank of Ethiopia, Awash Bank, etc.) with totals and transaction counts.
          </p>

          <button
            onClick={handleDownloadFinancialExcel}
            disabled={downloading === 'financial'}
            className="btn btn-success"
            style={{ width: '100%' }}
          >
            <Download size={16} />
            <span>{downloading === 'financial' ? 'Generating Workbook...' : 'Download Financial Excel'}</span>
          </button>
        </div>

        {/* 2. Lottery Sales Ledger Excel */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '14px' }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              background: 'var(--primary-surface)',
              color: 'var(--primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <FileSpreadsheet size={22} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.15rem' }}>Lottery Ticket Sales Ledger</h3>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Spreadsheet (.xlsx)</span>
            </div>
          </div>

          <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: '16px', lineHeight: 1.5 }}>
            Detailed sales log containing ticket numbers, buyer names, verified bank references,
            and purchase timestamps.
          </p>

          <div className="form-group" style={{ marginBottom: '16px' }}>
            <select
              className="form-select"
              value={selectedLotteryId}
              onChange={(e) => setSelectedLotteryId(e.target.value)}
            >
              {lotteries.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleDownloadLotterySalesExcel}
            disabled={downloading === 'lottery-sales' || !selectedLotteryId}
            className="btn btn-primary"
            style={{ width: '100%' }}
          >
            <Download size={16} />
            <span>{downloading === 'lottery-sales' ? 'Generating Workbook...' : 'Download Sales Ledger (.xlsx)'}</span>
          </button>
        </div>

        {/* 3. Executive PDF Summary */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '14px' }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              background: 'rgba(239, 68, 68, 0.12)',
              color: 'var(--rose)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <FileText size={22} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.15rem' }}>Executive PDF Summary</h3>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Executive Document (.pdf)</span>
            </div>
          </div>

          <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: '16px', lineHeight: 1.5 }}>
            Executive report summary generated with reportlab, complete with KPI cards,
            prize hierarchy distribution, and verified winners list.
          </p>

          <div className="form-group" style={{ marginBottom: '16px' }}>
            <select
              className="form-select"
              value={selectedLotteryId}
              onChange={(e) => setSelectedLotteryId(e.target.value)}
            >
              {lotteries.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleDownloadLotteryPdf}
            disabled={downloading === 'lottery-pdf' || !selectedLotteryId}
            className="btn btn-secondary"
            style={{ width: '100%' }}
          >
            <Download size={16} />
            <span>{downloading === 'lottery-pdf' ? 'Generating PDF...' : 'Download Executive PDF'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
