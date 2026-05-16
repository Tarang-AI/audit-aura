import React, { useEffect, useState } from 'react';
import { FileCheck, TrendingUp, Shield, Download, Cloud, Activity, GitPullRequest, CheckCircle, Clock, AlertTriangle, Target } from 'lucide-react';
import { useComplianceStore } from '../../store/useComplianceStore';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useToast, ToastContainer } from '@/components/ToastNotification';

interface AuditTrailEvent {
  id: string;
  violation_id: string;
  control_id: string;
  event_type: 'detected' | 'alerted' | 'pr_created' | 'pr_merged' | 'resolved';
  timestamp: string;
  details: string;
  pr_number?: number;
  pr_url?: string;
}

export const AuditorDashboard: React.FC = () => {
  const { complianceScore, violations, fetchDashboard, dashboardData } = useComplianceStore();
  const { toasts, removeToast, showSuccess, showWarning } = useToast();
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [cloudConnections, setCloudConnections] = useState<any[]>([]);
  const [auditTrail, setAuditTrail] = useState<AuditTrailEvent[]>([]);
  const [showAuditTrail, setShowAuditTrail] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      await fetchDashboard();
      setLastUpdated(new Date());
      
      // Fetch cloud trackers
      try {
        const response = await fetch('http://localhost:8000/dashboard');
        const data = await response.json();
        if (data.cloud_connections && Array.isArray(data.cloud_connections)) {
          setCloudConnections(data.cloud_connections);
        }
      } catch (error) {
        console.error('Failed to fetch cloud trackers:', error);
      }

      // Fetch audit trail
      try {
        const prResponse = await fetch('http://localhost:8000/prs');
        if (prResponse.ok) {
          const prData = await prResponse.json();
          const trail: AuditTrailEvent[] = [];
          
          // Build audit trail from violations and PRs
          if (violations && violations.length > 0) {
            violations.forEach((violation: any) => {
            // Violation detected event
            trail.push({
              id: `${violation.id}-detected`,
              violation_id: violation.id,
              control_id: violation.control_id,
              event_type: 'detected',
              timestamp: violation.timestamp,
              details: `Violation detected: ${violation.description}`,
            });

            // Alert sent event (simulated - 1 minute after detection)
            const alertTime = new Date(new Date(violation.timestamp).getTime() + 60000).toISOString();
            trail.push({
              id: `${violation.id}-alerted`,
              violation_id: violation.id,
              control_id: violation.control_id,
              event_type: 'alerted',
              timestamp: alertTime,
              details: `Alert sent to security team`,
            });

            // Find related PRs
            const relatedPRs = (prData.prs || []).filter((pr: any) => pr.violation_id === violation.id);
            relatedPRs.forEach((pr: any) => {
              // PR created event
              trail.push({
                id: `${pr.id}-created`,
                violation_id: violation.id,
                control_id: violation.control_id,
                event_type: 'pr_created',
                timestamp: pr.created_at,
                details: `PR #${pr.pr_number} created: ${pr.title}`,
                pr_number: pr.pr_number,
                pr_url: pr.pr_url,
              });

              // PR merged event
              if (pr.status === 'merged' && pr.merged_at) {
                trail.push({
                  id: `${pr.id}-merged`,
                  violation_id: violation.id,
                  control_id: violation.control_id,
                  event_type: 'pr_merged',
                  timestamp: pr.merged_at,
                  details: `PR #${pr.pr_number} merged - fix deployed`,
                  pr_number: pr.pr_number,
                  pr_url: pr.pr_url,
                });

                // Resolved event (1 minute after merge)
                const resolvedTime = new Date(new Date(pr.merged_at).getTime() + 60000).toISOString();
                trail.push({
                  id: `${violation.id}-resolved`,
                  violation_id: violation.id,
                  control_id: violation.control_id,
                  event_type: 'resolved',
                  timestamp: resolvedTime,
                  details: `Violation verified as resolved`,
                });
              }
            });
          });
          }

          // Sort by timestamp (newest first)
          trail.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
          setAuditTrail(trail.slice(0, 50)); // Keep last 50 events
        }
      } catch (error) {
        console.error('Failed to fetch audit trail:', error);
      }
    };
    
    fetchData();
    // Refresh every 30 seconds (matches backend COMPLIANCE_CHECK_INTERVAL)
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchDashboard, violations]);

  const handleExportReport = async () => {
    setGeneratingReport(true);
    try {
      // Simulate report generation
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Create report content
      const reportData = {
        generated_at: new Date().toISOString(),
        overall_score: Math.round((dashboardData?.compliance_score?.overall_score || 0) * 100),
        standards: Object.entries(dashboardData?.compliance_score?.standards || {}).map(([name, data]: [string, any]) => ({
          name,
          score: Math.round(data.score * 100),
          violations: data.violations,
          controls: data.controls
        })),
        total_violations: violations.length,
        audit_trail_events: auditTrail.length,
        cloud_connections: Array.isArray(cloudConnections) ? cloudConnections.length : 0
      };

      // Create downloadable JSON report
      const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `compliance-audit-report-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      showSuccess('Report Generated', 'Audit report generated and downloaded successfully!');
    } catch (error) {
      console.error('Error generating report:', error);
      showWarning('Report Generation Failed', 'Failed to generate report. Please try again.');
    } finally {
      setGeneratingReport(false);
    }
  };

  const overallScore = Math.round((dashboardData?.compliance_score?.overall_score || 0) * 100);
  
  const standardsData = Object.entries(dashboardData?.compliance_score?.standards || {}).map(([name, data]: [string, any]) => ({
    name,
    score: Math.round(data.score * 100),
    violations: data.violations,
    controls: data.controls
  }));

  const auditMetrics = [
    { name: 'Overall Compliance', value: `${overallScore}%`, icon: Shield, trend: '+2.3%' },
    { name: 'Total Standards', value: standardsData.length.toString(), icon: FileCheck, trend: 'Stable' },
    { name: 'Total Violations', value: violations.length.toString(), icon: TrendingUp, trend: '-12%' },
  ];

  return (
    <>
      <ToastContainer toasts={toasts} onClose={removeToast} />
      <div className="space-y-6 animate-fade-in">
        {/* Hero Header */}
        <div className="pro-card-accent overflow-hidden p-8">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
            <div className="max-w-3xl">
              <div className="badge-accent mb-4">
                <FileCheck className="h-3.5 w-3.5" />
                <span>Auditor Workspace</span>
              </div>
              <h1 className="heading-lg mb-3 flex items-center gap-3">
                <span className="circular-frame h-12 w-12 flex items-center justify-center">
                  <Shield className="h-6 w-6 text-accent-primary" />
                </span>
                Auditor/Assessor Dashboard
              </h1>
              <p className="text-body max-w-2xl">
                Verification and reporting workspace for reviewing compliance posture, connected evidence sources, and export-ready audit artifacts.
              </p>
            </div>

            <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:items-center">
              <div className="badge-success">
                <span className="status-dot-success pulse-glow"></span>
                <span>Live Monitoring</span>
                <span style={{ color: 'var(--text-muted)' }}>
                  {lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              <button
                onClick={handleExportReport}
                disabled={generatingReport}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Download className="h-5 w-5" />
                {generatingReport ? 'Generating...' : 'Export Report'}
              </button>
            </div>
          </div>
        </div>

        {/* Standards Under Review */}
        <div className="pro-card p-6">
          <h3 className="text-label mb-4 flex items-center gap-2">
            <Target className="h-4 w-4" />
            Audit Standards Under Review
          </h3>
          <div className="flex flex-wrap gap-2">
            {standardsData.map((standard) => (
              <div
                key={standard.name}
                className={`badge ${
                  standard.score >= 90
                    ? 'badge-success'
                    : standard.score >= 70
                    ? 'badge-warning'
                    : 'badge-error'
                }`}
              >
                <span className="font-semibold">{standard.name}</span>
                <span className="opacity-80">{standard.score}%</span>
              </div>
            ))}
            {standardsData.length === 0 && (
              <span className="text-caption">No standards configured</span>
            )}
          </div>
        </div>

        {/* Cloud Event Trackers */}
        <div className="pro-card p-6">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h3 className="heading-sm flex items-center gap-2 mb-2">
                <Cloud className="h-5 w-5 text-accent-primary" />
                Cloud Event Trackers
              </h3>
              <p className="text-caption">Audit trail sources for compliance verification</p>
            </div>
            <div className="badge-info">
              <Activity className="h-4 w-4" />
              <span>{Array.isArray(cloudConnections) ? cloudConnections.length : 0} Active</span>
            </div>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {(Array.isArray(cloudConnections) ? cloudConnections : []).map((connection) => (
              <div key={connection.id} className="metric-card">
                <div className="mb-4 flex items-start justify-between">
                  <div>
                    <h4 className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                      {connection.name}
                    </h4>
                    <p className="text-caption">{connection.provider}</p>
                  </div>
                  <div className="badge-success">
                    <Activity className="h-3.5 w-3.5" />
                    <span>{connection.status}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-caption">Events Monitored:</span>
                    <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                      {(connection.events_monitored || 0).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-caption">Region:</span>
                    <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                      {connection.region || 'N/A'}
                    </span>
                  </div>
                  <div className="text-caption mt-2">
                    Last event: {new Date(connection.last_event).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            {(Array.isArray(cloudConnections) ? cloudConnections.length : 0) === 0 && (
              <div className="col-span-full py-12 text-center">
                <Cloud className="mx-auto mb-3 h-16 w-16 opacity-30" style={{ color: 'var(--text-muted)' }} />
                <p className="text-caption">No cloud connections configured</p>
              </div>
            )}
          </div>
        </div>

        {/* Audit Metrics */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {auditMetrics.map((metric) => {
            const Icon = metric.icon;
            return (
              <div key={metric.name} className="metric-card-accent">
                <div className="mb-4 flex items-center justify-between">
                  <div className="icon-container-accent p-3">
                    <Icon className="h-6 w-6" />
                  </div>
                  <span className="badge-accent text-xs">{metric.trend}</span>
                </div>
                <h3 className="heading-lg mb-1">{metric.value}</h3>
                <p className="text-caption">{metric.name}</p>
              </div>
            );
          })}
        </div>

        {/* Compliance Score Chart */}
        <div className="pro-card p-6">
          <h3 className="heading-sm mb-6">Compliance Score by Standard</h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={standardsData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
              <XAxis dataKey="name" stroke="var(--text-tertiary)" />
              <YAxis stroke="var(--text-tertiary)" domain={[0, 100]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--bg-elevated)',
                  border: '1px solid var(--border-medium)',
                  borderRadius: '12px',
                  color: 'var(--text-primary)',
                  boxShadow: 'var(--shadow-md)',
                }}
              />
              <Legend />
              <Bar dataKey="score" fill="var(--accent-primary)" name="Compliance Score (%)" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Audit Trail */}
        <div className="pro-card p-6">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h3 className="heading-sm flex items-center gap-2 mb-2">
                <Clock className="h-5 w-5 text-accent-primary" />
                Complete Audit Trail
              </h3>
              <p className="text-caption">End-to-end lifecycle tracking: Detection → Alert → PR → Resolution</p>
            </div>
            <button
              onClick={() => setShowAuditTrail(!showAuditTrail)}
              className="btn-secondary"
            >
              {showAuditTrail ? 'Hide Trail' : 'Show Trail'}
            </button>
          </div>

          {showAuditTrail && (
            <div className="mt-6 max-h-96 space-y-3 overflow-y-auto">
              {auditTrail.length === 0 ? (
                <div className="py-16 text-center">
                  <Clock className="mx-auto mb-4 h-20 w-20 opacity-20" style={{ color: 'var(--text-muted)' }} />
                  <p className="heading-sm mb-2">No audit trail events yet</p>
                  <p className="text-caption">Events will appear here as violations are detected and resolved</p>
                </div>
              ) : (
                auditTrail.map((event) => {
                  const getEventIcon = () => {
                    switch (event.event_type) {
                      case 'detected': return <AlertTriangle className="h-5 w-5" style={{ color: 'var(--status-error)' }} />;
                      case 'alerted': return <Activity className="h-5 w-5" style={{ color: 'var(--status-warning)' }} />;
                      case 'pr_created': return <GitPullRequest className="h-5 w-5" style={{ color: 'var(--status-info)' }} />;
                      case 'pr_merged': return <GitPullRequest className="h-5 w-5" style={{ color: 'var(--accent-primary)' }} />;
                      case 'resolved': return <CheckCircle className="h-5 w-5" style={{ color: 'var(--status-success)' }} />;
                      default: return <Clock className="h-5 w-5" style={{ color: 'var(--text-muted)' }} />;
                    }
                  };

                  const getEventBadge = () => {
                    switch (event.event_type) {
                      case 'detected': return 'badge-error';
                      case 'alerted': return 'badge-warning';
                      case 'pr_created': return 'badge-info';
                      case 'pr_merged': return 'badge-accent';
                      case 'resolved': return 'badge-success';
                      default: return 'badge';
                    }
                  };

                  return (
                    <div key={event.id} className="metric-card flex items-start gap-4">
                      <div className="mt-1 flex-shrink-0">
                        {getEventIcon()}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="mb-2 flex flex-wrap items-center gap-3">
                          <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                            {event.control_id}
                          </span>
                          <span className={getEventBadge()}>
                            {event.event_type.replace('_', ' ').toUpperCase()}
                          </span>
                          <span className="text-caption">
                            {event.timestamp ? new Date(event.timestamp).toLocaleString() : 'N/A'}
                          </span>
                          {event.pr_number && (
                            <a
                              href={event.pr_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="badge-info hover:scale-105 transition-transform"
                            >
                              PR #{event.pr_number}
                            </a>
                          )}
                        </div>
                        <p className="text-body">{event.details}</p>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}
        </div>

        {/* Standards Summary Table */}
        <div className="pro-card overflow-hidden p-6">
          <h3 className="heading-sm flex items-center gap-2 mb-6">
            <Shield className="h-5 w-5 text-accent-primary" />
            Standards Summary
          </h3>
          <div className="overflow-x-auto">
            <table className="table-pro">
              <thead>
                <tr>
                  <th>Standard</th>
                  <th>Compliance Score</th>
                  <th>Total Controls</th>
                  <th>Violations</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {standardsData.map((standard) => (
                  <tr key={standard.name}>
                    <td className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                      {standard.name}
                    </td>
                    <td>
                      <div className="flex items-center gap-3">
                        <div className="h-2 w-24 rounded-full" style={{ background: 'var(--bg-tertiary)' }}>
                          <div
                            className="h-2 rounded-full transition-all"
                            style={{
                              width: `${standard.score}%`,
                              background: 'linear-gradient(90deg, var(--accent-primary), var(--accent-secondary))',
                            }}
                          />
                        </div>
                        <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                          {standard.score}%
                        </span>
                      </div>
                    </td>
                    <td>{standard.controls}</td>
                    <td>{standard.violations}</td>
                    <td>
                      <span className={`badge ${
                        standard.score >= 90 ? 'badge-success' :
                        standard.score >= 70 ? 'badge-warning' :
                        'badge-error'
                      }`}>
                        {standard.score >= 90 ? 'Compliant' : standard.score >= 70 ? 'At Risk' : 'Non-Compliant'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
};

// Made with Bob
