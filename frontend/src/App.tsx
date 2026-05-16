import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate as BaseNavigate } from 'react-router-dom';
import { withAppId } from './utils/appParam';

const Navigate = ({ to, ...props }: any) => <BaseNavigate {...props} to={withAppId(to)} />;
import { Layout } from './components/Layout';
import { ErrorBoundary } from './components/ErrorBoundary';
import { LoadingSpinner } from './components/LoadingSpinner';
import SkillAcquisitionAnimation from './components/SkillAcquisitionAnimation';
import { useWebSocket } from './hooks/useWebSocket';

// Pages
import { AdminDashboard } from './pages/admin/Dashboard';
import { AdminControls } from './pages/admin/Controls';
import { AdminSettings } from './pages/admin/Settings';
import { AdminConnections } from './pages/admin/Connections';
import { AdminViolations } from './pages/admin/Violations';
import AdminSkills from './pages/admin/Skills';
import { UserDashboard } from './pages/user/Dashboard';
import { UserViolations } from './pages/user/Violations';
import { AuditorDashboard } from './pages/auditor/Dashboard';
import { AuditorReports } from './pages/auditor/Reports';
import { SecurityDashboard } from './pages/security/Dashboard';
import { SecurityIncidents } from './pages/security/Incidents';
import { PRTracking } from './pages/security/PRTracking';
import { Login } from './pages/Login';
import { RoleSelector } from './pages/RoleSelector';

// Types
export type UserRole = 'admin' | 'devops' | 'auditor' | 'security' | null;

interface User {
  role: Exclude<UserRole, null>;
  name: string;
  email: string;
}

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [newSkills, setNewSkills] = useState<any[]>([]);

  // WebSocket connection for real-time updates
  const { lastMessage } = useWebSocket();

  useEffect(() => {
    // Check for stored user session
    const storedUser = localStorage.getItem('audit-aura_user');
    if (storedUser) {
      try {
        const parsed = JSON.parse(storedUser);
        setUser(parsed);
      } catch (error) {
        console.error('Failed to parse stored user:', error);
        localStorage.removeItem('audit-aura_user');
      }
    }
    setLoading(false);
  }, []);

  // Handle WebSocket messages for skill acquisition
  useEffect(() => {
    if (lastMessage) {
      try {
        const message = JSON.parse(lastMessage);
        if (message.type === 'skills_acquired' && message.data?.skills) {
          setNewSkills(message.data.skills);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    }
  }, [lastMessage]);

  const handleLogin = (role: UserRole, name: string, email: string) => {
    if (!role) {
      return;
    }

    const newUser: User = { role, name, email };
    setUser(newUser);
    // Store user session (in production, use secure tokens)
    localStorage.setItem('audit-aura_user', JSON.stringify(newUser));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('audit-aura_user');
  };

  if (loading) {
    return <LoadingSpinner fullScreen />;
  }

  return (
    <ErrorBoundary>
      {/* Skill Acquisition Animation */}
      {newSkills.length > 0 && (
        <SkillAcquisitionAnimation
          skills={newSkills}
          onComplete={() => setNewSkills([])}
        />
      )}

      <BrowserRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={
            user ? <Navigate to="/" replace /> : <Login onLogin={handleLogin} />
          } />
          
          <Route path="/select-role" element={
            user ? <Navigate to="/" replace /> : <RoleSelector onSelect={handleLogin} />
          } />

          {/* Protected Routes */}
          {!user ? (
            <Route path="*" element={<Navigate to="/select-role" replace />} />
          ) : (
            <Route element={<Layout user={user} onLogout={handleLogout} />}>
              {/* Admin Routes */}
              {user.role === 'admin' && (
                <>
                  <Route path="/" element={<AdminDashboard />} />
                  <Route path="/admin/dashboard" element={<AdminDashboard />} />
                  <Route path="/admin/controls" element={<AdminControls />} />
                  <Route path="/admin/connections" element={<AdminConnections />} />
                  <Route path="/admin/violations" element={<AdminViolations />} />
                  <Route path="/admin/skills" element={<AdminSkills />} />
                  <Route path="/admin/settings" element={<AdminSettings />} />
                </>
              )}

              {/* DevOps Engineer Routes */}
              {user.role === 'devops' && (
                <>
                  <Route path="/" element={<UserDashboard />} />
                  <Route path="/devops/dashboard" element={<UserDashboard />} />
                  <Route path="/devops/violations" element={<UserViolations />} />
                </>
              )}

              {/* Auditor Routes */}
              {user.role === 'auditor' && (
                <>
                  <Route path="/" element={<AuditorDashboard />} />
                  <Route path="/auditor/dashboard" element={<AuditorDashboard />} />
                  <Route path="/auditor/reports" element={<AuditorReports />} />
                </>
              )}

              {/* Security Team Routes */}
              {user.role === 'security' && (
                <>
                  <Route path="/" element={<SecurityDashboard />} />
                  <Route path="/security/dashboard" element={<SecurityDashboard />} />
                  <Route path="/security/incidents" element={<SecurityIncidents />} />
                  <Route path="/security/pr-tracking" element={<PRTracking />} />
                </>
              )}

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          )}
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;

// Made with Bob
