import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { AppLink as Link } from './AppLink';
import { Shield, LogOut, Menu, X, Bell, Settings, BarChart3, FileText, AlertTriangle, GitPullRequest, Activity, Cloud, Zap, Home, Link as LinkIcon, Calendar } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';

interface LayoutProps {
  user: {
    role: 'admin' | 'devops' | 'auditor' | 'security';
    name: string;
    email: string;
  };
  onLogout: () => void;
}

export const Layout: React.FC<LayoutProps> = ({ user, onLogout }) => {
  const [sidebarOpen, setSidebarOpen] = React.useState(true);
  const location = useLocation();

  const navigation = {
    admin: [
      { name: 'Dashboard', href: '/admin/dashboard', icon: BarChart3 },
      { name: 'Controls', href: '/admin/controls', icon: FileText },
      { name: 'Connections', href: '/admin/connections', icon: Cloud },
      { name: 'Violations', href: '/admin/violations', icon: AlertTriangle },
      { name: 'Skills', href: '/admin/skills', icon: Zap },
      { name: 'Settings', href: '/admin/settings', icon: Settings },
    ],
    devops: [
      { name: 'Dashboard', href: '/devops/dashboard', icon: BarChart3 },
      { name: 'My Violations', href: '/devops/violations', icon: AlertTriangle },
    ],
    auditor: [
      { name: 'Dashboard', href: '/auditor/dashboard', icon: BarChart3 },
      { name: 'Reports', href: '/auditor/reports', icon: FileText },
    ],
    security: [
      { name: 'Dashboard', href: '/security/dashboard', icon: BarChart3 },
      { name: 'Incidents', href: '/security/incidents', icon: AlertTriangle },
      { name: 'PR Tracking', href: '/security/pr-tracking', icon: GitPullRequest },
    ],
  };

  const navItems = navigation[user.role] || [];

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      {/* Modern Top Navigation Bar */}
      <nav className="glass-minimal fixed inset-x-0 top-0 z-30 border-b" style={{ borderColor: 'var(--border-default)' }}>
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between gap-4">
            {/* Left Section */}
            <div className="flex min-w-0 items-center gap-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="btn-ghost p-2 transition-all duration-200"
                aria-label="Toggle sidebar"
              >
                {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>

              <div className="flex min-w-0 items-center gap-3">
                {/* Modern Logo with Gradient */}
                <div className="circular-frame h-10 w-10 flex items-center justify-center">
                  <Shield className="h-5 w-5" />
                </div>
                <div className="min-w-0">
                  <h1 className="text-lg font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>
                    AuditAura
                  </h1>
                  <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                    Compliance Intelligence
                  </p>
                </div>
              </div>
            </div>

            {/* Right Section */}
            <div className="flex items-center gap-3">
              {/* Status Badge */}
              <div className="badge-success hidden md:flex">
                <span className="status-dot-success pulse-glow"></span>
                <span>System Active</span>
              </div>

              {/* Theme Toggle */}
              <ThemeToggle />

              {/* Notifications */}
              <button className="btn-ghost relative p-2 transition-all duration-200">
                <Bell className="h-5 w-5" />
                <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full" style={{ background: 'var(--status-error)', boxShadow: '0 0 8px var(--status-error)' }}></span>
              </button>

              {/* User Profile */}
              <div className="card-glass flex items-center gap-3 px-3 py-2">
                <div className="hidden h-9 w-9 items-center justify-center rounded-xl font-semibold sm:flex icon-box-accent">
                  {user.name.charAt(0).toUpperCase()}
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                    {user.name}
                  </p>
                  <p className="text-xs capitalize" style={{ color: 'var(--text-tertiary)' }}>
                    {user.role}
                  </p>
                </div>
                <button
                  onClick={onLogout}
                  className="btn-ghost p-2 transition-all duration-200"
                  title="Logout"
                >
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Modern Sidebar - Inspired by Reference */}
      <aside
        className={`glass-minimal fixed inset-y-0 left-0 z-20 w-64 border-r pt-16 transform transition-all duration-300 ease-in-out ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        style={{ borderColor: 'var(--border-default)' }}
      >
        {/* Workspace Info */}
        <div className="border-b px-4 py-5" style={{ borderColor: 'var(--border-default)' }}>
          <div className="card-gradient p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-label">Workspace</p>
                <p className="mt-1 text-sm font-semibold capitalize" style={{ color: 'var(--text-primary)' }}>
                  {user.role} Portal
                </p>
              </div>
              <div className="badge-success">
                <span className="status-dot-success"></span>
                Active
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Links - Modern Icon Style */}
        <nav className="mt-4 space-y-1 px-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'card-gradient scale-[1.02]'
                    : 'hover:bg-opacity-50'
                }`}
                style={{
                  color: isActive ? 'var(--text-primary)' : 'var(--text-tertiary)',
                  background: isActive ? undefined : 'transparent',
                }}
              >
                <div
                  className={`flex h-9 w-9 items-center justify-center rounded-xl transition-all duration-200 ${
                    isActive ? 'icon-box-accent' : 'icon-box'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                </div>
                <span className="flex-1">{item.name}</span>
                {isActive && (
                  <span className="h-2 w-2 rounded-full" style={{ background: 'var(--accent-primary)', boxShadow: '0 0 8px var(--accent-primary)' }}></span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* System Health Footer */}
        <div className="absolute bottom-0 left-0 right-0 border-t p-4" style={{ borderColor: 'var(--border-default)' }}>
          <div className="card-glass p-4">
            <div className="flex items-center justify-between text-xs mb-3">
              <span className="text-label">System Health</span>
              <div className="badge-success">
                <span className="status-dot-success"></span>
                <span>Operational</span>
              </div>
            </div>
            <div className="space-y-2 text-xs" style={{ color: 'var(--text-tertiary)' }}>
              <div className="flex items-center justify-between">
                <span>Uptime</span>
                <span className="font-mono font-semibold" style={{ color: 'var(--text-primary)' }}>
                  99.9%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Monitoring</span>
                <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                  Active
                </span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main
        className={`pt-16 transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-0'}`}
      >
        <div className="px-4 py-6 sm:px-6 lg:px-8">
          <div className="mx-auto w-full max-w-[1600px]">
            <Outlet />
          </div>
        </div>
      </main>

      {/* Ambient Background Effects */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div
          className="absolute top-0 left-1/4 w-96 h-96 rounded-full blur-3xl animate-float opacity-20"
          style={{ background: 'radial-gradient(circle, var(--accent-primary) 0%, transparent 70%)' }}
        ></div>
        <div
          className="absolute bottom-0 right-1/4 w-96 h-96 rounded-full blur-3xl animate-float opacity-15"
          style={{
            background: 'radial-gradient(circle, var(--accent-secondary) 0%, transparent 70%)',
            animationDelay: '1.5s',
          }}
        ></div>
      </div>
    </div>
  );
};

// Made with Bob
