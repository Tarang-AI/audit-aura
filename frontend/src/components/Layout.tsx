import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { AppLink as Link } from './AppLink';
import { Shield, LogOut, Menu, X, Bell, Settings, BarChart3, FileText, Users, AlertTriangle, GitPullRequest, Activity, Cloud, Zap } from 'lucide-react';
import { theme } from '@/config/theme';

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
      { name: 'Agent Skills', href: '/admin/skills', icon: Zap },
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

  const getRoleColor = () => {
    switch (user.role) {
      case 'admin': return 'from-purple-500 to-pink-500';
      case 'devops': return 'from-blue-500 to-cyan-500';
      case 'auditor': return 'from-green-500 to-emerald-500';
      case 'security': return 'from-red-500 to-orange-500';
      default: return 'from-gray-500 to-gray-600';
    }
  };

  return (
    <div className={`min-h-screen ${theme.bg.primary}`}>
      {/* Top Navigation - Professional Header */}
      <nav className={`glass-strong fixed w-full z-30 top-0 border-b shadow-lg shadow-black/20 ${theme.border.primary}`}>
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className={`p-2 rounded-lg ${theme.text.muted} hover:text-cyan-400 ${theme.bg.hover} focus:outline-none focus:ring-2 focus:ring-cyan-500 transition-all duration-200`}
              >
                {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </button>
              <div className="flex items-center ml-4 group">
                <div className="relative">
                  <Shield className="h-8 w-8 text-cyan-400 " />
                  <div className="absolute inset-0 bg-cyan-400/20 blur-xl rounded-full "></div>
                </div>
                <div className="ml-3">
                  <span className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                    AuditAura
                  </span>
                  <div className="flex items-center gap-1 mt-0.5">
                    <Activity className="h-3 w-3 text-green-400 animate-pulse" />
                    <span className="text-xs text-green-400 font-medium">Live</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Notification Bell */}
              <button className={`relative p-2 rounded-lg ${theme.text.muted} hover:text-cyan-400 ${theme.bg.hover} transition-all duration-200 group`}>
                <Bell className="h-6 w-6" />
                <span className="absolute top-1 right-1 flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                  <span className={`relative inline-flex rounded-full h-3 w-3 bg-red-500 border-2 ${theme.bg.primary}`}></span>
                </span>
              </button>
              
              {/* User Profile */}
              <div className="flex items-center gap-3 glass rounded-lg px-3 py-2">
                <div className="text-right">
                  <p className={`text-sm font-medium ${theme.text.primary}`}>{user.name}</p>
                  <p className={`text-xs font-semibold bg-gradient-to-r ${getRoleColor()} bg-clip-text text-transparent capitalize`}>
                    {user.role}
                  </p>
                </div>
                <button
                  onClick={onLogout}
                  className={`p-2 rounded-lg ${theme.text.muted} hover:text-red-400 ${theme.bg.hover} transition-all duration-200`}
                  title="Logout"
                >
                  <LogOut className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Sidebar - Modern Glass with Neon Accents */}
      <div className={`fixed inset-y-0 left-0 z-20 w-64 glass-strong border-r ${theme.border.primary} pt-16 transform transition-transform duration-300 ease-in-out ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        {/* Workspace */}
        <div className={`px-4 py-4 border-b ${theme.border.primary}`}>
          <div className={`glass-card p-3 bg-gradient-to-r ${getRoleColor()} bg-opacity-10`}>
            <div className="flex items-center gap-2">
              <div className="relative">
                <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
                <div className="absolute inset-0 w-2 h-2 rounded-full bg-green-400 animate-ping"></div>
              </div>
              <span className={`text-sm font-semibold ${theme.text.primary} capitalize`}>{user.role} Portal</span>
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="mt-5 px-3 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`group flex items-center px-3 py-3 text-sm font-medium rounded-xl transition-all duration-200 relative overflow-hidden ${
                  isActive
                    ? 'glass-strong text-cyan-400 border border-cyan-500/20 bg-cyan-500/10'
                    : `${theme.text.muted} hover:text-cyan-400 ${theme.bg.hover}`
                }`}
              >
                {isActive && (
                  <>
                    <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-purple-500/10"></div>
                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-cyan-400 to-purple-400 rounded-r"></div>
                  </>
                )}
                <Icon className={`mr-3 h-5 w-5 transition-transform duration-200 ${isActive ? 'text-cyan-400 scale-110' : `${theme.text.muted} group-hover:text-cyan-400 group-hover:scale-110`}`} />
                <span className="relative z-10">{item.name}</span>
                {isActive && (
                  <div className="ml-auto">
                    <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></div>
                  </div>
                )}
              </Link>
            );
          })}
        </nav>

        {/* System Health Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-white/10">
          <div className="glass rounded-lg p-3">
            <div className="flex items-center justify-between text-xs">
              <span className="text-dark-500">System Health</span>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
                <span className="text-green-400 font-medium">Operational</span>
              </div>
            </div>
            <div className="mt-2 flex items-center justify-between text-xs text-dark-500">
              <span>Uptime</span>
              <span className="font-mono text-cyan-400">99.9%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className={`pt-16 transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-0'}`}>
        <div className="py-6 px-4 sm:px-6 lg:px-8">
          <Outlet />
        </div>
      </main>

      {/* Ambient Background Effects */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl animate-float"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl animate-float" style={{ animationDelay: '1s' }}></div>
      </div>
    </div>
  );
};

// Made with Bob
