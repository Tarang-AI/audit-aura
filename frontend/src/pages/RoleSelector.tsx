import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, User, FileCheck, ArrowRight, ShieldAlert, Sparkles } from 'lucide-react';
import { UserRole } from '../App';
import { theme } from '@/config/theme';

interface RoleSelectorProps {
  onSelect: (role: UserRole, name: string, email: string) => void;
}

export const RoleSelector: React.FC<RoleSelectorProps> = ({ onSelect }) => {
  const navigate = useNavigate();

  const roles = [
    {
      id: 'admin' as UserRole,
      name: 'Compliance Manager',
      description: 'Strategic oversight: Manage compliance standards, upload PDFs, and configure system settings',
      icon: Shield,
      gradient: 'from-orange-500 to-amber-500',
      path: '/admin/dashboard',
    },
    {
      id: 'devops' as UserRole,
      name: 'DevOps Engineer',
      description: 'Tactical execution: View assigned violations, track fixes, and receive real-time alerts',
      icon: User,
      gradient: 'from-blue-500 to-cyan-500',
      path: '/devops/dashboard',
    },
    {
      id: 'security' as UserRole,
      name: 'Security Analyst',
      description: 'Operational monitoring: Investigate security incidents, coordinate remediation, and track PRs',
      icon: ShieldAlert,
      gradient: 'from-red-500 to-orange-500',
      path: '/security/dashboard',
    },
    {
      id: 'auditor' as UserRole,
      name: 'Auditor/Assessor',
      description: 'Verification & reporting: Review compliance reports, generate audit evidence, and export data',
      icon: FileCheck,
      gradient: 'from-green-500 to-emerald-500',
      path: '/auditor/dashboard',
    },
  ];

  const handleRoleSelect = (role: UserRole, roleName: string) => {
    // Get user info from localStorage (set during login)
    const storedUser = localStorage.getItem('user');
    let email = 'demo@auditaura.com';
    let name = 'Demo User';
    
    if (storedUser) {
      try {
        const parsed = JSON.parse(storedUser);
        email = parsed.email || email;
        name = parsed.name || name;
      } catch (e) {
        console.error('Failed to parse user:', e);
      }
    }
    
    // Call the onSelect callback to update App state
    onSelect(role, name, email);
  };

  return (
    <div className={`min-h-screen ${theme.bg.primary} flex items-center justify-center p-4 relative overflow-hidden`}>
      {/* Animated background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl animate-float"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-orange-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '1s' }}></div>
        <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-pink-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }}></div>
      </div>

      <div className="max-w-6xl w-full relative z-10">
        {/* Header */}
        <div className="text-center mb-12 animate-fadeIn">
          <div className="inline-flex items-center justify-center mb-6 relative">
            <div className="absolute inset-0 bg-cyan-500/20 blur-2xl rounded-full animate-pulse-slow"></div>
            <div className="relative glass-strong p-4 rounded-2xl">
              <Shield className="h-12 w-12 text-cyan-400" />
            </div>
          </div>
          <h1 className="text-5xl font-bold mb-3">
            <span className="bg-gradient-to-r from-cyan-400 via-orange-400 to-amber-400 bg-clip-text text-transparent">
              Welcome to AuditAura
            </span>
          </h1>
          <p className={`text-xl ${theme.text.secondary} flex items-center justify-center gap-2`}>
            <Sparkles className="h-5 w-5 text-cyan-400" />
            Select your role to continue
            <Sparkles className="h-5 w-5 text-orange-400" />
          </p>
        </div>

        {/* Role Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {roles.map((role, index) => {
            const Icon = role.icon;
            
            return (
              <div
                key={role.id}
                className="glass-card p-8 hover-lift cursor-pointer group relative overflow-hidden animate-slideUp data-stream"
                style={{ animationDelay: `${index * 100}ms` }}
                onClick={() => handleRoleSelect(role.id, role.name)}
              >
                {/* Gradient border effect on hover */}
                <div className={`absolute inset-0 bg-gradient-to-r ${role.gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-300`}></div>
                
                {/* Top accent line with pulse effect */}
                <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${role.gradient} group-hover:h-2 transition-all duration-300`}></div>
                
                <div className="relative z-10">
                  <div className={`inline-flex items-center justify-center w-16 h-16 rounded-xl mb-6 bg-gradient-to-r ${role.gradient} p-[2px] group-hover:scale-110 transition-transform duration-300`}>
                    <div className={`w-full h-full ${theme.bg.primary} rounded-xl flex items-center justify-center`}>
                      <Icon className="h-8 w-8 text-cyan-400 group-hover:text-white transition-colors" />
                    </div>
                  </div>
                  
                  <h3 className={`text-2xl font-bold ${theme.text.primary} mb-3 group-hover:text-cyan-400 transition-colors`}>
                    {role.name}
                  </h3>
                  <p className={`${theme.text.secondary} mb-6 min-h-[60px] leading-relaxed`}>
                    {role.description}
                  </p>
                  
                  <div className={`flex items-center gap-2 font-medium bg-gradient-to-r ${role.gradient} bg-clip-text text-transparent group-hover:gap-4 transition-all`}>
                    <span>Continue as {role.name}</span>
                    <ArrowRight className="h-5 w-5 text-cyan-400 group-hover:translate-x-2 transition-transform" />
                  </div>
                </div>

                {/* Hover glow effect */}
                <div className={`absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none`}>
                  <div className={`absolute inset-0 bg-gradient-to-r ${role.gradient} blur-xl opacity-20`}></div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="mt-12 text-center animate-fadeIn" style={{ animationDelay: '400ms' }}>
          <div className="glass rounded-lg px-6 py-3 inline-block">
            <p className={`${theme.text.secondary} text-sm flex items-center gap-2`}>
              <Shield className="h-4 w-4 text-cyan-400" />
              Need help? Contact your system administrator
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Made with Bob
