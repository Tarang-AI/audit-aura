import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Lock, Mail } from 'lucide-react';
import { theme } from '@/config/theme';

interface LoginProps {
  onLogin: (role: any, name: string, email: string) => void;
}

export const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // Mock authentication - in production, this would call an API
    localStorage.setItem('user', JSON.stringify({ email, name: 'Demo User' }));
    const { withAppId } = await import('@/utils/appParam');
    navigate(withAppId('/select-role'));
  };

  return (
    <div className={`min-h-screen ${theme.bg.primary} flex items-center justify-center p-4 relative overflow-hidden`}>
      {/* Animated background gradient orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl animate-float"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }}></div>
      </div>

      <div className="max-w-md w-full relative z-10">
        {/* Logo and Title */}
        <div className="text-center mb-8 animate-fadeIn">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-cyan-500 to-purple-600 rounded-2xl mb-4 shadow-lg shadow-cyan-500/20">
            <Shield className="h-8 w-8 text-white" />
          </div>
          <h1 className={`text-3xl font-bold ${theme.text.primary} mb-2 bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent`}>
            AuditAura
          </h1>
          <p className={theme.text.secondary}>Continuous Compliance Guardian</p>
        </div>

        {/* Login Form */}
        <div className={`${theme.bg.card} rounded-2xl shadow-xl p-8 border ${theme.border.primary} backdrop-blur-xl animate-slideUp`}>
          <h2 className={`text-2xl font-bold ${theme.text.primary} mb-6`}>Welcome Back</h2>
          
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>
                Email Address
              </label>
              <div className="relative">
                <Mail className={`absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 ${theme.text.muted}`} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={`w-full pl-10 pr-4 py-3 ${theme.input.bg} ${theme.input.border} ${theme.input.text} border rounded-lg ${theme.input.focus} focus:ring-2 transition-all`}
                  placeholder="you@example.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>
                Password
              </label>
              <div className="relative">
                <Lock className={`absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 ${theme.text.muted}`} />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={`w-full pl-10 pr-4 py-3 ${theme.input.bg} ${theme.input.border} ${theme.input.text} border rounded-lg ${theme.input.focus} focus:ring-2 transition-all`}
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center">
                <input type="checkbox" className={`rounded ${theme.input.border} text-cyan-500 focus:ring-cyan-500`} />
                <span className={`ml-2 text-sm ${theme.text.secondary}`}>Remember me</span>
              </label>
              <a href="#" className="text-sm text-cyan-400 hover:text-cyan-300 transition-colors">
                Forgot password?
              </a>
            </div>

            <button
              type="submit"
              className={`w-full ${theme.button.primary} py-3 rounded-lg font-medium transition-all duration-200 hover:scale-105 shadow-lg shadow-cyan-500/20`}
            >
              Sign In
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className={`text-sm ${theme.text.secondary}`}>
              Don't have an account?{' '}
              <a href="#" className="text-cyan-400 hover:text-cyan-300 font-medium transition-colors">
                Sign up
              </a>
            </p>
          </div>
        </div>

        {/* Demo Notice */}
        <div className={`mt-6 text-center text-sm ${theme.text.muted} ${theme.bg.card} rounded-lg p-3 border ${theme.border.primary}`}>
          <p>🎭 Demo Mode: Use any email/password to login</p>
        </div>
      </div>
    </div>
  );
};

// Made with Bob
