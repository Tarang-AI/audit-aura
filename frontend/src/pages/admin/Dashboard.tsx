import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  Clock,
  Cloud,
  FileText,
  GitBranch,
  MoreHorizontal,
  RefreshCw,
  Server,
  Shield,
  Upload,
} from 'lucide-react';
import {
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useComplianceStore } from '../../store/useComplianceStore';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { useToast, ToastContainer } from '@/components/ToastNotification';

interface DashboardKpi {
  label: string;
  value: string;
  tone: 'neutral' | 'critical' | 'warning' | 'success';
  helper?: string;
}

interface CollapsibleSectionProps {
  title: string;
  description: string;
  defaultOpen?: boolean;
  badge?: string;
  children: React.ReactNode;
}

interface MetricCardProps {
  label: string;
  value: string;
  helper?: string;
  tone?: 'neutral' | 'critical' | 'warning' | 'success';
}

interface SeverityBadgeProps {
  severity: 'critical' | 'high' | 'medium' | 'low';
}

const sectionCardClassName = 'rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6';
const subCardClassName = 'rounded-xl border border-slate-200 bg-slate-50 p-4';

const toneClasses: Record<NonNullable<MetricCardProps['tone']>, string> = {
  neutral: 'border-slate-200 bg-white text-slate-900',
  critical: 'border-red-200 bg-red-50 text-red-900',
  warning: 'border-amber-200 bg-amber-50 text-amber-900',
  success: 'border-emerald-200 bg-emerald-50 text-emerald-900',
};

const severityBadgeClasses: Record<SeverityBadgeProps['severity'], string> = {
  critical: 'bg-red-100 text-red-800 border border-red-200',
  high: 'bg-orange-100 text-orange-800 border border-orange-200',
  medium: 'bg-amber-100 text-amber-800 border border-amber-200',
  low: 'bg-blue-100 text-blue-800 border border-blue-200',
};

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
  title,
  description,
  defaultOpen = false,
  badge,
  children,
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <section className={sectionCardClassName}>
      <button
        type="button"
        onClick={() => setIsOpen((current) => !current)}
        className="flex w-full items-start justify-between gap-4 text-left"
      >
        <div className="min-w-0">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
            {badge ? (
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                {badge}
              </span>
            ) : null}
          </div>
          <p className="mt-1 text-sm text-slate-500">{description}</p>
        </div>

        <div className="mt-0.5 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500">
          {isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </div>
      </button>

      {isOpen ? <div className="mt-5">{children}</div> : null}
    </section>
  );
};

const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  helper,
  tone = 'neutral',
}) => (
  <div className={`rounded-xl border p-4 shadow-sm ${toneClasses[tone]}`}>
    <p className="text-sm font-medium text-slate-500">{label}</p>
    <p className="mt-2 text-2xl font-semibold tracking-tight">{value}</p>
    {helper ? <p className="mt-1 text-xs text-slate-500">{helper}</p> : null}
  </div>
);

const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity }) => (
  <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${severityBadgeClasses[severity]}`}>
    {severity}
  </span>
);

const AdminDashboard: React.FC = () => {
  const { complianceScore, violations, loading, fetchDashboard, dashboardData } = useComplianceStore();
  const [uploading, setUploading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [cloudConnections, setCloudConnections] = useState<any[]>([]);
  const [driftData, setDriftData] = useState<any>({
    total_drifts: 0,
    critical_drifts: 0,
    high_drifts: 0,
    medium_drifts: 0,
    drift_by_source: {},
  });
  const [personaInsights, setPersonaInsights] = useState<any>({
    priority_actions: [],
    kpis: {
      drift_resolution_rate: 0,
      mean_time_to_detect_drift: '0 hours',
      mean_time_to_remediate: '0 hours',
      compliance_score_trend: 'stable',
    },
  });
  const [activeProvider, setActiveProvider] = useState<string>('AWS');
  const [showMoreActions, setShowMoreActions] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const fetchData = async () => {
      if (!isMounted) return;

      await fetchDashboard();

      if (!isMounted) return;
      setLastUpdated(new Date());

      try {
        const response = await fetch('http://localhost:8000/dashboard');
        const data = await response.json();

        if (!isMounted) return;

        if (data.cloud_connections && Array.isArray(data.cloud_connections)) {
          setCloudConnections(data.cloud_connections);
        }

        if (data.configuration_drift) {
          setDriftData(data.configuration_drift);
        }

        if (data.persona_insights?.admin) {
          setPersonaInsights(data.persona_insights.admin);
        }
      } catch (error) {
        if (!isMounted) return;
        console.error('Failed to fetch dashboard data:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [fetchDashboard]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchDashboard();
    setLastUpdated(new Date());
    setTimeout(() => setRefreshing(false), 500);
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        await fetchDashboard();
        setLastUpdated(new Date());
        showSuccess('Upload Successful', 'PDF uploaded successfully!');
      } else {
        const error = await response.json();
        showWarning('Upload Failed', error.detail || 'Unknown error');
      }
    } catch (error) {
      console.error('Upload error:', error);
      showWarning('Upload Failed', 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  const totalControls = dashboardData?.compliance_score?.total_controls || 0;
  const totalViolations = dashboardData?.compliance_score?.total_violations || violations.length || 0;
  // Handle both decimal (0.78) and percentage (78) formats
  const overallScore = dashboardData?.compliance_score?.overall_score
    ? (dashboardData.compliance_score.overall_score > 1
        ? dashboardData.compliance_score.overall_score / 100
        : dashboardData.compliance_score.overall_score)
    : (complianceScore > 1 ? complianceScore / 100 : complianceScore);
  const compliancePercentage = Math.round(overallScore * 100);
  const criticalDrifts = driftData?.critical_drifts || 0;
  const highDrifts = driftData?.high_drifts || 0;
  const unresolvedCriticalAndHigh = criticalDrifts + highDrifts;

  const standardsData = Object.entries(dashboardData?.compliance_score?.standards || {}).map(
    ([name, data]: [string, any]) => ({
      name,
      score: Math.round(data.score * 100),
      violations: data.violations,
      controls: data.controls,
    }),
  );

  const trendData = [
    { time: '00:00', score: 85 },
    { time: '04:00', score: 87 },
    { time: '08:00', score: 82 },
    { time: '12:00', score: 88 },
    { time: '16:00', score: compliancePercentage },
    { time: '20:00', score: compliancePercentage },
  ];

  const severityData = [
    { name: 'Critical', value: (violations || []).filter((v: any) => v.severity === 'critical').length, color: '#dc2626' },
    { name: 'High', value: (violations || []).filter((v: any) => v.severity === 'high').length, color: '#ea580c' },
    { name: 'Medium', value: (violations || []).filter((v: any) => v.severity === 'medium').length, color: '#d97706' },
    { name: 'Low', value: (violations || []).filter((v: any) => v.severity === 'low').length, color: '#2563eb' },
  ];

  const riskStatus = unresolvedCriticalAndHigh > 0 || totalViolations > 0
    ? unresolvedCriticalAndHigh >= 4 || totalViolations >= 6
      ? 'high'
      : 'medium'
    : 'low';

  const riskBannerClasses = {
    high: 'border-red-200 bg-red-50 text-red-900',
    medium: 'border-amber-200 bg-amber-50 text-amber-900',
    low: 'border-emerald-200 bg-emerald-50 text-emerald-900',
  };

  const riskLabel = riskStatus === 'high' ? 'HIGH RISK' : riskStatus === 'medium' ? 'MODERATE RISK' : 'LOW RISK';
  const riskMessage = unresolvedCriticalAndHigh > 0
    ? `${unresolvedCriticalAndHigh} critical drifts unresolved`
    : totalViolations > 0
      ? `${totalViolations} active violations require review`
      : 'No critical drifts currently unresolved';

  const dashboardKpis: DashboardKpi[] = [
    {
      label: 'Compliance Score',
      value: `${compliancePercentage}%`,
      tone: compliancePercentage >= 90 ? 'success' : compliancePercentage >= 70 ? 'warning' : 'critical',
      helper: compliancePercentage >= 90 ? 'Strong control posture' : 'Needs continued attention',
    },
    {
      label: 'Active Violations',
      value: `${totalViolations}`,
      tone: totalViolations > 0 ? 'critical' : 'success',
      helper: totalViolations > 0 ? 'Open compliance findings' : 'No open findings',
    },
    {
      label: 'Critical Drifts',
      value: `${criticalDrifts}`,
      tone: criticalDrifts > 0 ? 'critical' : 'success',
      helper: `${highDrifts} additional high-severity drifts`,
    },
    {
      label: 'Last Updated',
      value: lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      tone: 'neutral',
      helper: lastUpdated.toLocaleDateString([], { month: 'short', day: 'numeric' }),
    },
  ];

  const criticalConfigurationDrifts = useMemo(() => {
    const recentDrifts = Array.isArray(driftData?.recent_drifts) ? driftData.recent_drifts : [];

    return recentDrifts
      .filter(
        (drift: any) =>
          drift &&
          drift.remediation_status !== 'resolved' &&
          (drift.severity === 'critical' || drift.severity === 'high'),
      )
      .sort((left: any, right: any) => new Date(right.timestamp).getTime() - new Date(left.timestamp).getTime());
  }, [driftData]);

  const groupedSources = useMemo(() => {
    return (Array.isArray(cloudConnections) ? cloudConnections : []).reduce((acc: Record<string, any[]>, connection: any) => {
      if (!acc[connection.provider]) {
        acc[connection.provider] = [];
      }
      acc[connection.provider].push(connection);
      return acc;
    }, {});
  }, [cloudConnections]);

  const providerNames = Object.keys(groupedSources);

  useEffect(() => {
    if (!providerNames.length) return;
    if (!activeProvider || !groupedSources[activeProvider]) {
      setActiveProvider(providerNames[0]);
    }
  }, [activeProvider, groupedSources, providerNames]);

  // Move loading check after all hooks
  if (loading && !complianceScore) {
    return <LoadingSpinner fullScreen message="Loading dashboard..." />;
  }

  const activeProviderConnections = groupedSources[activeProvider] || [];

  return (
    <div className="space-y-6">
      <header className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-900 text-white shadow-sm">
                <Shield className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500">Executive Compliance Overview</p>
                <h1 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
                  Compliance Manager Dashboard
                </h1>
              </div>
            </div>
          </div>

          <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:flex-wrap sm:justify-end">
            <label className="cursor-pointer">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileUpload}
                className="hidden"
                disabled={uploading}
              />
              <span className="inline-flex min-h-[42px] items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800">
                {uploading ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4" />
                    Upload PDF
                  </>
                )}
              </span>
            </label>

            <button
              type="button"
              onClick={handleRefresh}
              disabled={refreshing}
              className="inline-flex min-h-[42px] items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </button>

            <button
              type="button"
              className="inline-flex min-h-[42px] items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50"
            >
              <FileText className="h-4 w-4" />
              Generate Report
            </button>

            <div className="relative">
              <button
                type="button"
                onClick={() => setShowMoreActions((current) => !current)}
                className="inline-flex min-h-[42px] items-center justify-center rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-slate-600 shadow-sm transition hover:bg-slate-50"
                aria-label="More actions"
              >
                <MoreHorizontal className="h-4 w-4" />
              </button>

              {showMoreActions ? (
                <div className="absolute right-0 z-10 mt-2 w-48 rounded-xl border border-slate-200 bg-white p-2 shadow-lg">
                  <button
                    type="button"
                    className="flex w-full items-center rounded-lg px-3 py-2 text-left text-sm text-slate-700 transition hover:bg-slate-50"
                  >
                    Add Standard
                  </button>
                  <button
                    type="button"
                    className="flex w-full items-center rounded-lg px-3 py-2 text-left text-sm text-slate-700 transition hover:bg-slate-50"
                  >
                    Add Connection
                  </button>
                  <button
                    type="button"
                    className="flex w-full items-center rounded-lg px-3 py-2 text-left text-sm text-slate-700 transition hover:bg-slate-50"
                  >
                    Export Data
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </header>

      <section className={`rounded-2xl border p-5 shadow-sm sm:p-6 ${riskBannerClasses[riskStatus]}`}>
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] opacity-80">Overall Risk Status</p>
            <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
              <h2 className="text-2xl font-semibold tracking-tight">{riskLabel}</h2>
              <span className="text-sm font-medium opacity-90">{riskMessage}</span>
            </div>
          </div>

          <div className="inline-flex items-center gap-2 rounded-xl border border-current/10 bg-white/60 px-4 py-3 text-sm font-medium">
            <AlertTriangle className="h-4 w-4" />
            {criticalDrifts} critical drifts · {totalViolations} active violations
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {dashboardKpis.map((kpi) => (
          <MetricCard
            key={kpi.label}
            label={kpi.label}
            value={kpi.value}
            helper={kpi.helper}
            tone={kpi.tone}
          />
        ))}
      </section>

      <section className={sectionCardClassName}>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Priority Actions</h2>
            <p className="mt-1 text-sm text-slate-500">
              Immediate actions surfaced from current compliance posture and drift activity.
            </p>
          </div>
          <div className="text-sm text-slate-500">
            {personaInsights.priority_actions?.length || 0} active recommendations
          </div>
        </div>

        <div className="mt-5 space-y-3">
          {personaInsights.priority_actions?.length > 0 ? (
            personaInsights.priority_actions.map((action: string, index: number) => {
              const actionTone =
                index === 0 ? 'critical' : index === 1 ? 'warning' : 'neutral';

              return (
                <div
                  key={`${action}-${index}`}
                  className={`rounded-xl border p-4 shadow-sm ${toneClasses[actionTone as keyof typeof toneClasses]}`}
                >
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">
                        {index + 1}
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">{action}</p>
                        <p className="mt-1 text-sm text-slate-500">
                          Prioritized from current admin insights and unresolved operational risk.
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 transition hover:bg-slate-50"
                      >
                        View Details
                      </button>
                      <button
                        type="button"
                        className="rounded-lg bg-slate-900 px-3 py-2 text-xs font-medium text-white transition hover:bg-slate-800"
                      >
                        Take Action
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="rounded-xl border border-dashed border-emerald-200 bg-emerald-50 p-5 text-sm text-emerald-800">
              No priority actions at this time. Current monitoring data does not indicate urgent executive follow-up.
            </div>
          )}
        </div>

        {personaInsights.kpis ? (
          <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="Resolution Rate"
              value={`${personaInsights.kpis.drift_resolution_rate}%`}
              helper="Drifts resolved within operational targets"
              tone="success"
            />
            <MetricCard
              label="Mean Time to Detect"
              value={personaInsights.kpis.mean_time_to_detect_drift}
              helper="Average time to identify drift"
              tone="neutral"
            />
            <MetricCard
              label="Mean Time to Remediate"
              value={personaInsights.kpis.mean_time_to_remediate}
              helper="Average remediation duration"
              tone="neutral"
            />
            <MetricCard
              label="Score Trend"
              value={personaInsights.kpis.compliance_score_trend === 'declining' ? 'Declining' : 'Improving'}
              helper="Directional posture signal"
              tone={personaInsights.kpis.compliance_score_trend === 'declining' ? 'critical' : 'success'}
            />
          </div>
        ) : null}
      </section>

      <section className={sectionCardClassName}>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Critical Configuration Drifts</h2>
            <p className="mt-1 text-sm text-slate-500">
              Unresolved critical and high-severity configuration drifts, newest first.
            </p>
          </div>
          <div className="text-sm text-slate-500">
            {criticalConfigurationDrifts.length} unresolved critical/high items
          </div>
        </div>

        <div className="mt-5 space-y-3">
          {criticalConfigurationDrifts.length > 0 ? (
            criticalConfigurationDrifts.map((drift: any) => (
              <div
                key={drift.id}
                className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
              >
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <SeverityBadge severity={drift.severity} />
                      <h3 className="font-semibold text-slate-900">{drift.resource_name}</h3>
                      <span className="text-sm text-slate-500">{drift.resource_type}</span>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-slate-600">{drift.drift_details}</p>

                    <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
                      <div className={subCardClassName}>
                        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Detected By</p>
                        <p className="mt-1 text-sm font-medium text-slate-900">{drift.detected_by}</p>
                      </div>
                      <div className={subCardClassName}>
                        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Status</p>
                        <p className="mt-1 text-sm font-medium capitalize text-slate-900">
                          {drift.remediation_status.replace('_', ' ')}
                        </p>
                      </div>
                      <div className={subCardClassName}>
                        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Detected</p>
                        <p className="mt-1 text-sm font-medium text-slate-900">
                          {new Date(drift.timestamp).toLocaleString([], {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </p>
                      </div>
                    </div>

                    {drift.compliance_impact?.length ? (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {drift.compliance_impact.map((standard: string) => (
                          <span
                            key={standard}
                            className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600"
                          >
                            {standard}
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 transition hover:bg-slate-50"
                    >
                      View Details
                    </button>
                    <button
                      type="button"
                      className="rounded-lg bg-slate-900 px-3 py-2 text-xs font-medium text-white transition hover:bg-slate-800"
                    >
                      Take Action
                    </button>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="rounded-xl border border-dashed border-emerald-200 bg-emerald-50 p-5 text-sm text-emerald-800">
              No unresolved critical or high-severity configuration drifts detected.
            </div>
          )}
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.4fr_1fr]">
        <div className={sectionCardClassName}>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-slate-900">Compliance Trend</h2>
              <p className="mt-1 text-sm text-slate-500">24-hour compliance score movement.</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-slate-500">Current Score</p>
              <p className="text-2xl font-semibold text-slate-900">{compliancePercentage}%</p>
            </div>
          </div>

          <div className="mt-5 h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData} margin={{ top: 10, right: 12, left: -12, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="time"
                  stroke="#64748b"
                  tick={{ fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  stroke="#64748b"
                  domain={[0, 100]}
                  tick={{ fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '12px',
                    boxShadow: '0 10px 30px rgba(15, 23, 42, 0.08)',
                  }}
                  labelStyle={{ color: '#0f172a' }}
                  itemStyle={{ color: '#0f172a' }}
                />
                <ReferenceLine y={90} stroke="#16a34a" strokeDasharray="4 4" />
                <ReferenceLine y={70} stroke="#d97706" strokeDasharray="4 4" />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#0f172a"
                  strokeWidth={3}
                  dot={{ fill: '#0f172a', stroke: '#ffffff', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, fill: '#0f172a', stroke: '#ffffff', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-5 grid grid-cols-2 gap-3 border-t border-slate-200 pt-4 sm:grid-cols-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">24h Change</p>
              <p className={`mt-1 text-sm font-semibold ${compliancePercentage - trendData[0].score >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>
                {compliancePercentage - trendData[0].score >= 0 ? '+' : ''}
                {Math.abs(compliancePercentage - trendData[0].score)}%
              </p>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Threshold</p>
              <p className="mt-1 text-sm font-semibold text-slate-900">70% operational baseline</p>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Updated</p>
              <p className="mt-1 text-sm font-semibold text-slate-900">
                {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        </div>

        <div className={sectionCardClassName}>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-slate-900">Violations by Severity</h2>
              <p className="mt-1 text-sm text-slate-500">Current open violations by severity tier.</p>
            </div>
            <div className="rounded-xl bg-slate-100 px-3 py-2 text-sm font-medium text-slate-700">
              {totalViolations} total
            </div>
          </div>

          <div className="mt-5 h-[300px]">
            {totalViolations > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={severityData}
                    cx="50%"
                    cy="50%"
                    innerRadius={62}
                    outerRadius={92}
                    dataKey="value"
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {severityData.map((entry, index) => (
                      <Cell
                        key={`severity-${index}`}
                        fill={entry.color}
                        stroke="#ffffff"
                        strokeWidth={2}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      border: '1px solid #e2e8f0',
                      borderRadius: '12px',
                      boxShadow: '0 10px 30px rgba(15, 23, 42, 0.08)',
                    }}
                    labelStyle={{ color: '#0f172a' }}
                    itemStyle={{ color: '#0f172a' }}
                    formatter={(value, name) => [
                      `${value} violations (${Math.round((Number(value) / totalViolations) * 100)}%)`,
                      name,
                    ]}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full flex-col items-center justify-center rounded-xl border border-dashed border-emerald-200 bg-emerald-50 px-4 text-center">
                <CheckCircle className="h-10 w-10 text-emerald-600" />
                <p className="mt-3 text-sm font-medium text-emerald-800">No violations detected</p>
                <p className="mt-1 text-sm text-emerald-700">Current standards are operating without open findings.</p>
              </div>
            )}
          </div>

          <div className="mt-5 space-y-2 border-t border-slate-200 pt-4">
            {severityData.map((item) => (
              <div key={item.name} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2 text-slate-600">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                  {item.name}
                </div>
                <span className="font-medium text-slate-900">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className={sectionCardClassName}>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Standards Overview</h2>
            <p className="mt-1 text-sm text-slate-500">
              Framework-level compliance summary with score and violation count.
            </p>
          </div>
          <div className="text-sm text-slate-500">{standardsData.length} standards tracked</div>
        </div>

        {standardsData.length > 0 ? (
          <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {standardsData.map((standard) => (
              <div key={standard.name} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="font-semibold text-slate-900">{standard.name}</h3>
                    <p className="mt-1 text-sm text-slate-500">Compliance framework</p>
                  </div>
                  <span
                    className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                      standard.score >= 90
                        ? 'bg-emerald-100 text-emerald-800'
                        : standard.score >= 70
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {standard.score}%
                  </span>
                </div>

                <div className="mt-4 flex items-end justify-between">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Violations</p>
                    <p className="mt-1 text-2xl font-semibold text-slate-900">{standard.violations}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Controls</p>
                    <p className="mt-1 text-sm font-semibold text-slate-700">{standard.controls}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-5 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
            <Shield className="mx-auto h-10 w-10 text-slate-400" />
            <p className="mt-3 text-sm font-medium text-slate-700">No compliance standards configured</p>
            <p className="mt-1 text-sm text-slate-500">
              Upload a compliance PDF to populate standards and framework tracking.
            </p>
          </div>
        )}
      </section>

      <CollapsibleSection
        title="Cloud Event Monitoring"
        description="Real-time monitoring of connected cloud providers and event sources."
        badge={`${Array.isArray(cloudConnections) ? cloudConnections.length : 0} connections`}
      >
        {providerNames.length > 0 ? (
          <div className="space-y-5">
            <div className="flex flex-wrap gap-2">
              {providerNames.map((provider) => (
                <button
                  key={provider}
                  type="button"
                  onClick={() => setActiveProvider(provider)}
                  className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
                    activeProvider === provider
                      ? 'bg-slate-900 text-white'
                      : 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  {provider} ({groupedSources[provider].length})
                </button>
              ))}
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <MetricCard
                label="Events Monitored"
                value={`${activeProviderConnections.reduce((sum: number, item: any) => sum + (item.events_monitored || 0), 0)}`}
                helper="Across selected provider"
              />
              <MetricCard
                label="Config Changes"
                value={`${activeProviderConnections.reduce((sum: number, item: any) => sum + (item.config_changes_detected || 0), 0)}`}
                helper="Detected recent changes"
                tone="warning"
              />
              <MetricCard
                label="Healthy"
                value={`${activeProviderConnections.filter((item: any) => item.health === 'healthy').length}`}
                helper="Healthy sources"
                tone="success"
              />
              <MetricCard
                label="Unhealthy"
                value={`${activeProviderConnections.filter((item: any) => item.health === 'unhealthy').length}`}
                helper="Sources requiring review"
                tone={activeProviderConnections.filter((item: any) => item.health === 'unhealthy').length > 0 ? 'critical' : 'neutral'}
              />
            </div>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {activeProviderConnections.map((connection: any) => (
                <div key={connection.id} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <Cloud className="h-4 w-4 text-slate-500" />
                        <h4 className="font-semibold text-slate-900">{connection.region}</h4>
                        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium capitalize text-slate-600">
                          {connection.status}
                        </span>
                      </div>
                      <p className="mt-2 text-sm text-slate-500">{connection.description}</p>
                    </div>
                    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${
                      connection.health === 'healthy'
                        ? 'bg-emerald-100 text-emerald-800'
                        : connection.health === 'warning'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-red-100 text-red-800'
                    }`}>
                      {connection.health}
                    </span>
                  </div>

                  <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                    <div className={subCardClassName}>
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Events</p>
                      <p className="mt-1 font-semibold text-slate-900">{(connection.events_monitored || 0).toLocaleString()}</p>
                    </div>
                    <div className={subCardClassName}>
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Changes</p>
                      <p className="mt-1 font-semibold text-slate-900">{connection.config_changes_detected}</p>
                    </div>
                    <div className={subCardClassName}>
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Last Event</p>
                      <p className="mt-1 font-semibold text-slate-900">
                        {new Date(connection.last_event).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </p>
                    </div>
                    <div className={subCardClassName}>
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Provider</p>
                      <p className="mt-1 font-semibold text-slate-900">{connection.provider}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
            <Server className="mx-auto h-10 w-10 text-slate-400" />
            <p className="mt-3 text-sm font-medium text-slate-700">No cloud event sources configured</p>
            <p className="mt-1 text-sm text-slate-500">
              Connect a cloud provider to monitor configuration changes in real time.
            </p>
          </div>
        )}
      </CollapsibleSection>

      <CollapsibleSection
        title="Recent Violations"
        description="Latest compliance violations captured from monitored systems."
        badge={`${violations.length} items`}
      >
        {violations.length > 0 ? (
          <div className="space-y-3">
            {violations.slice(0, 5).map((violation: any, index: number) => (
              <div key={`${violation.control_id}-${index}`} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <SeverityBadge severity={violation.severity} />
                      <h4 className="font-semibold text-slate-900">{violation.control_id}</h4>
                      <span className="text-sm text-slate-500">{violation.standard}</span>
                    </div>
                    <p className="mt-2 text-sm text-slate-600">{violation.description}</p>

                    <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
                      <div className={subCardClassName}>
                        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Detected</p>
                        <p className="mt-1 text-sm font-semibold text-slate-900">
                          {new Date(violation.timestamp).toLocaleString([], {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </p>
                      </div>
                      <div className={subCardClassName}>
                        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Category</p>
                        <p className="mt-1 text-sm font-semibold text-slate-900">{violation.category || 'Compliance'}</p>
                      </div>
                      <div className={subCardClassName}>
                        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Status</p>
                        <p className="mt-1 text-sm font-semibold text-slate-900">
                          {violation.resolved ? 'Resolved' : 'Open'}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 transition hover:bg-slate-50"
                    >
                      View Details
                    </button>
                    <button
                      type="button"
                      className="rounded-lg bg-slate-900 px-3 py-2 text-xs font-medium text-white transition hover:bg-slate-800"
                    >
                      Take Action
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-emerald-200 bg-emerald-50 p-5 text-sm text-emerald-800">
            No recent violations detected across monitored standards.
          </div>
        )}
      </CollapsibleSection>

      <CollapsibleSection
        title="Audit Logs"
        description="Operational summary for executive review based on current dashboard activity."
        badge="Summary"
      >
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Last Refresh" value={lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} helper="Dashboard sync time" />
          <MetricCard label="Total Controls" value={`${totalControls}`} helper="Controls currently tracked" />
          <MetricCard label="Standards" value={`${standardsData.length}`} helper="Frameworks represented" />
          <MetricCard label="Drift Sources" value={`${Object.keys(driftData?.drift_by_source || {}).length}`} helper="Sources with observed drift" />
        </div>
      </CollapsibleSection>

      <CollapsibleSection
        title="Infrastructure Details"
        description="Underlying infrastructure and monitoring source details."
        badge={`${Object.keys(driftData?.drift_by_source || {}).length} sources`}
      >
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <h4 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
              <GitBranch className="h-4 w-4" />
              Drift by Source
            </h4>
            <div className="mt-4 space-y-3">
              {Object.keys(driftData?.drift_by_source || {}).length > 0 ? (
                Object.entries(driftData.drift_by_source).map(([source, count]: [string, any]) => (
                  <div key={source} className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                    <span className="text-sm font-medium text-slate-700">{source}</span>
                    <span className="text-sm font-semibold text-slate-900">{count}</span>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-500">No drift source breakdown available.</p>
              )}
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <h4 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
              <Clock className="h-4 w-4" />
              Monitoring Snapshot
            </h4>
            <div className="mt-4 space-y-3">
              <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                <span className="text-sm font-medium text-slate-700">Connections</span>
                <span className="text-sm font-semibold text-slate-900">{cloudConnections.length}</span>
              </div>
              <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                <span className="text-sm font-medium text-slate-700">Total Drifts</span>
                <span className="text-sm font-semibold text-slate-900">{driftData?.total_drifts || 0}</span>
              </div>
              <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                <span className="text-sm font-medium text-slate-700">Medium Drifts</span>
                <span className="text-sm font-semibold text-slate-900">{driftData?.medium_drifts || 0}</span>
              </div>
              <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                <span className="text-sm font-medium text-slate-700">Active Provider</span>
                <span className="text-sm font-semibold text-slate-900">{activeProvider || 'N/A'}</span>
              </div>
            </div>
          </div>
        </div>
      </CollapsibleSection>
    </div>
  );
};

export { AdminDashboard };

// Made with Bob
