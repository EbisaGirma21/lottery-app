import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';
import { AuditLogs } from './pages/AuditLogs';
import { Dashboard } from './pages/Dashboard';
import { DrawExecution } from './pages/DrawExecution';
import { Login } from './pages/Login';
import { Lotteries } from './pages/Lotteries';
import { Participants } from './pages/Participants';
import { PaymentQueue } from './pages/PaymentQueue';
import { Reports } from './pages/Reports';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Auth Route */}
          <Route path="/login" element={<Login />} />

          {/* Protected Admin Routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/lotteries" element={<Lotteries />} />
              <Route path="/participants" element={<Participants />} />
              <Route path="/payments" element={<PaymentQueue />} />
              <Route path="/draws" element={<DrawExecution />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/audit-logs" element={<AuditLogs />} />
            </Route>
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
