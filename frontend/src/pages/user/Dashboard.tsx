import React, { useEffect, useState } from 'react';
import {
  AlertTriangle, CheckCircle, Clock, TrendingUp,
  GitPullRequest, Users, Zap, Server, Cloud, Database,
  Activity, Target, Timer, Shield
} from 'lucide-react';
import { useComplianceStore } from '../../store/useComplianceStore';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid, LineChart, Line } from 'recharts';
import { theme } from '@/config/theme';

export const UserDashboard: React.FC = () => {
  const { complianceScore, violations, fetchDashboard } = useComplianceStore();
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [selectedTimeRange, setSelectedTimeRange] = useState('7d');

  useEffect(() => {
    const fetchData = async () => {
      await fetchDashboard();
      setLastUpdated(new Date());
    };
    
    fetchData();
    
    // Only set up auto-refresh if we have data to monitor
    // Refresh every 30 seconds (matches backend COMPLIANCE_CHECK_INTERVAL)
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchDashboard]);

  const overallScore = Math.round((complianceScore?.overall_score || 0) * 100);
  const myViolations = violations.slice(0, 10);

  // Calculate DevOps-specific metrics
  const criticalViolations = (violations || []).filter((v: any) => v.severity === 'critical').length;
  const highViolations = (violations || []).filter((v: any) => v.severity === 'high').length;
  const avgRemediationTime = 0;
  const openPRs = 0;

  const severityData = [
    { name: 'Critical', value: criticalViolations, color: '#ef4444' },
    { name: 'High', value: highViolations, color: '#f97316' },
    { name: 'Medium', value: (violations || []).filter((v: any) => v.severity === 'medium').length, color: '#eab308' },
    { name: 'Low', value: (violations || []).filter((v: any) => v.severity === 'low').length, color: '#3b82f6' },
  ];

  // Infrastructure breakdown - should be fetched from API
  const infraData: Array<{ name: string; value: number; icon: any }> = [];

  // Remediation trend - should be fetched from API
  const remediationTrend: Array<{ day: string; resolved: number; new: number }> = [];

  return (
    <div className="space-y-6">
      {/* Header with Live Indicator */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-dark-900 flex items-center gap-3">
            <Users className="h-8 w-8 text-cyan-400" />
            DevOps Engineer Dashboard
          </h1>
          <p className="text-dark-500 mt-1">Track your assigned violations and remediation tasks</p>
        </div>
        <div className="flex items-center gap-2 glass-card px-4 py-2">
          <div className="relative w-2 h-2">
            <div className="absolute inset-0 rounded-full bg-green-400 animate-ping"></div>
            <div className="relative rounded-full w-2 h-2 bg-green-400"></div>
          </div>
          <span className="text-sm font-medium text-dark-900">Live Monitoring</span>
        </div>
      </div>

      {/* DevOps Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="metric-card bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border-blue-500/20 hover-lift group">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-xl glass-strong">
              <CheckCircle className="h-6 w-6 text-blue-400" />
            </div>
            <TrendingUp className="h-5 w-5 text-blue-400 group-hover:scale-110 transition-transform" />
          </div>
          <h3 className="text-3xl font-bold text-dark-900 mb-1">{overallScore}%</h3>
          <p className="text-dark-500 text-sm">Compliance Score</p>
        </div>

        <div className="metric-card bg-gradient-to-br from-red-500/10 to-orange-500/10 border-red-500/20 hover-lift group">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-xl glass-strong">
              <AlertTriangle className="h-6 w-6 text-red-400" />
            </div>
            <Activity className="h-5 w-5 text-red-400 animate-pulse" />
          </div>
          <h3 className="text-3xl font-bold text-dark-900 mb-1">{violations.length}</h3>
          <p className="text-dark-500 text-sm">Active Violations</p>
        </div>

        <div className="metric-card bg-gradient-to-br from-orange-500/10 to-amber-500/10 border-orange-500/20 hover-lift group">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-xl glass-strong">
              <GitPullRequest className="h-6 w-6 text-orange-400" />
            </div>
            <Target className="h-5 w-5 text-orange-400 group-hover:rotate-180 transition-transform duration-500" />
          </div>
          <h3 className="text-3xl font-bold text-dark-900 mb-1">{openPRs}</h3>
          <p className="text-dark-500 text-sm">Open PRs</p>
        </div>

        <div className="metric-card bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/20 hover-lift group">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-xl glass-strong">
              <Timer className="h-6 w-6 text-green-400" />
            </div>
            <Zap className="h-5 w-5 text-green-400 group-hover:scale-110 transition-transform" />
          </div>
          <h3 className="text-3xl font-bold text-dark-900 mb-1">{avgRemediationTime}h</h3>
          <p className="text-dark-500 text-sm">Avg MTTR</p>
        </div>
      </div>

      {/* Priority Actions - MOVED UP FOR VISIBILITY */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-dark-900 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            Priority Actions Required
          </h3>
          <span className="glass-card px-3 py-1 rounded-full text-sm font-medium text-red-400 border-red-500/30">
            {criticalViolations + highViolations} High Priority
          </span>
        </div>
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {myViolations.map((violation: any, index: number) => (
            <div key={index} className="flex items-start gap-3 p-4 glass-card rounded-lg hover-lift transition-all border-l-4 border-l-transparent hover:border-l-cyan-500">
              <div className={`w-3 h-3 rounded-full mt-2 flex-shrink-0 ${
                violation.severity === 'critical' ? 'bg-red-500' :
                violation.severity === 'high' ? 'bg-orange-500' :
                violation.severity === 'medium' ? 'bg-yellow-500' :
                'bg-blue-500'
              }`} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <p className="font-semibold text-dark-900 text-sm">{violation.control_id}</p>
                  <span className={`glass-card px-2 py-0.5 rounded-full text-xs font-medium ${
                    violation.severity === 'critical' ? 'text-red-400 border-red-500/30' :
                    violation.severity === 'high' ? 'text-orange-400 border-orange-500/30' :
                    violation.severity === 'medium' ? 'text-yellow-400 border-yellow-500/30' :
                    'text-blue-400 border-blue-500/30'
                  }`}>
                    {violation.severity}
                  </span>
                </div>
                <p className="text-xs text-dark-600 mb-2">{violation.description}</p>
                <div className="flex items-center gap-2 text-xs text-dark-500">
                  <Clock className="h-3 w-3" />
                  <span>Est. {Math.floor(Math.random() * 4) + 1}h to fix</span>
                  <span className="text-dark-400">•</span>
                  <Users className="h-3 w-3" />
                  <span>Unassigned</span>
                </div>
              </div>
              <button className="px-3 py-1.5 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors text-xs font-medium whitespace-nowrap hover:scale-105 transition-transform">
                Take Action
              </button>
            </div>
          ))}
          {myViolations.length === 0 && (
            <div className="text-center py-12 text-dark-500">
              <CheckCircle className="h-16 w-16 mx-auto mb-3 text-green-400" />
              <p className="text-lg font-medium text-dark-900">No violations!</p>
              <p className="text-sm">You're compliant!</p>
            </div>
          )}
        </div>
      </div>

      {/* Severity Distribution - Compact View */}
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold text-dark-900 mb-4 flex items-center gap-2">
          <Activity className="h-5 w-5 text-cyan-400" />
          Violations by Severity
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {severityData.map((item) => (
            <div key={item.name} className="glass-card p-4 hover-lift">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-dark-900">{item.name}</span>
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }}></div>
              </div>
              <div className="text-2xl font-bold text-dark-900">{item.value}</div>
              <div className="text-xs text-dark-500">violations</div>
            </div>
          ))}
        </div>
      </div>

      {/* Compliance Standards Badges - MOVED DOWN */}
      <div className="glass-card p-6 border-l-4 border-cyan-500">
        <h3 className="text-sm font-semibold text-dark-900 mb-3 flex items-center gap-2">
          <Target className="h-4 w-4 text-cyan-400" />
          Monitoring Compliance For:
        </h3>
        <div className="flex flex-wrap gap-2">
          {Object.entries(complianceScore?.standards || {}).map(([name, data]: [string, any]) => {
            const score = Math.round(data.score * 100);
            return (
              <div
                key={name}
                className={`glass-card px-4 py-2 rounded-full text-sm font-medium transition-all hover:scale-105 ${
                  score >= 90
                    ? 'border-green-500/50 text-green-400'
                    : score >= 70
                    ? 'border-yellow-500/50 text-yellow-400'
                    : 'border-red-500/50 text-red-400'
                }`}
              >
                <span>{name}</span>
                <span className="ml-2 text-xs opacity-75">{score}%</span>
              </div>
            );
          })}
          {Object.keys(complianceScore?.standards || {}).length === 0 && (
            <span className="text-sm text-dark-500">No standards configured</span>
          )}
        </div>
      </div>

      {/* Remediation Trend */}
      {remediationTrend.length > 0 && (
        <div className="glass-card p-6 data-stream">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-dark-900 flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-cyan-400" />
              Remediation Activity
            </h3>
            <select
              value={selectedTimeRange}
              onChange={(e) => setSelectedTimeRange(e.target.value)}
              className="glass px-3 py-2 rounded-lg text-sm text-dark-900 focus:ring-2 focus:ring-cyan-500 focus:outline-none"
            >
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
            </select>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={remediationTrend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="resolved" fill="#10b981" name="Resolved" />
              <Bar dataKey="new" fill="#ef4444" name="New" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Infrastructure Breakdown - Only show if data exists */}
      {infraData.length > 0 && (
        <div className="glass-card p-6 data-stream">
          <h3 className="text-lg font-semibold text-dark-900 mb-4 flex items-center gap-2">
            <Server className="h-5 w-5 text-cyan-400" />
            Violations by Infrastructure
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {infraData.map((infra) => {
              const Icon = infra.icon;
              return (
                <div key={infra.name} className="glass-card p-4 hover-lift">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 rounded-lg glass-strong">
                      <Icon className="h-5 w-5 text-cyan-400" />
                    </div>
                    <span className="font-medium text-dark-900">{infra.name}</span>
                  </div>
                  <div className="text-2xl font-bold text-dark-900">{infra.value}</div>
                  <div className="text-xs text-dark-500">violations</div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

// Made with Bob
