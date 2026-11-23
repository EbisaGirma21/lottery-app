import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

export const Layout: React.FC = () => {
  const location = useLocation();

  const getPageTitle = (path: string): string => {
    if (path === '/') return 'Executive Dashboard & Overview';
    if (path.startsWith('/lotteries')) return 'Lotteries & Ticket Allocation';
    if (path.startsWith('/payments')) return 'Manual Payment Verification Queue';
    if (path.startsWith('/draws')) return 'Cryptographic Draw & Winner Engine';
    if (path.startsWith('/reports')) return 'Reports, Analytics & Financial Exports';
    if (path.startsWith('/audit-logs')) return 'System Audit Trail & Access Logs';
    return 'Lottery Operations Platform';
  };

  return (
    <div className="app-container">
      <Sidebar />
      <div className="main-content">
        <Topbar title={getPageTitle(location.pathname)} />
        <main className="page-container">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
