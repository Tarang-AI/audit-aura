import React, { useEffect, useState } from 'react';
import { AlertTriangle, Search, Filter, CheckCircle, XCircle, Clock, ArrowRight, FileText, GitPullRequest, ExternalLink } from 'lucide-react';
import { useComplianceStore } from '../../store/useComplianceStore';
import { theme } from '@/config/theme';

export const SecurityIncidents: React.FC = () => {
  const { violations, fetchDashboard } = useComplianceStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedViolation, setSelectedViolation] = useState<any>(null);
  const [violationPRs, setViolationPRs] = useState<Record<string, any[]>>({});

  useEffect(() => {
    fetchDashboard();
    fetchAllPRs();
    const interval = setInterval(() => {
      fetchDashboard();
      fetchAllPRs();
    }, 30000);
    return () => clearInterval(interval);
  }, [fetchDashboard]);

  const fetchAllPRs = async () => {
    try {
      const response = await fetch('http://localhost:8000/prs');
      if (response.ok) {
        const prs = await response.json();
        // Group PRs by violation_id
        const prsByViolation: Record<string, any[]> = {};
        prs.forEach((pr: any) => {
          if (pr.violation_id) {
            if (!prsByViolation[pr.violation_id]) {
              prsByViolation[pr.violation_id] = [];
            }
            prsByViolation[pr.violation_id].push(pr);
          }
        });
        setViolationPRs(prsByViolation);
      }
    } catch (error) {
      console.error('Failed to fetch PRs:', error);
      setViolationPRs({});
    }
  };

  const categories = ['all', ...Array.from(new Set(violations.map((v: any) => v.category)))];

  const filteredViolations = (violations || []).filter((v: any) => {
    const matchesSearch = v.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         v.control_id?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSeverity = selectedSeverity === 'all' || v.severity === selectedSeverity;
    const matchesCategory = selectedCategory === 'all' || v.category === selectedCategory;
    return matchesSearch && matchesSeverity && matchesCategory;
  });

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  const getSeverityBadgeColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-700 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'low': return 'bg-blue-100 text-cyan-400 border-blue-200';
      default: return `${theme.bg.tertiary} ${theme.text.secondary} ${theme.border.primary}`;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className={`text-3xl font-bold ${theme.text.primary}`}>Security Incidents</h1>
        <p className={`${theme.text.secondary} mt-1`}>Investigate and remediate compliance violations</p>
      </div>

      {/* Filters */}
      <div className={`${theme.bg.card} rounded-xl shadow-sm p-4`}>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-2 relative">
            <Search className={`absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 ${theme.text.muted}`} />
            <input
              type="text"
              placeholder="Search incidents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className={`w-full pl-10 pr-4 py-2 border ${theme.border.secondary} rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
            />
          </div>
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className={`px-4 py-2 border ${theme.border.secondary} rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className={`px-4 py-2 border ${theme.border.secondary} rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
          >
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat === 'all' ? 'All Categories' : cat}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className={`${theme.bg.card} rounded-lg shadow-sm p-4 border-l-4 border-red-500`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme.text.secondary}`}>Critical</p>
              <p className={`text-2xl font-bold ${theme.text.primary}`}>
                {(violations || []).filter((v: any) => v.severity === 'critical').length}
              </p>
            </div>
            <AlertTriangle className="h-8 w-8 text-red-500" />
          </div>
        </div>
        <div className={`${theme.bg.card} rounded-lg shadow-sm p-4 border-l-4 border-orange-500`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme.text.secondary}`}>High</p>
              <p className={`text-2xl font-bold ${theme.text.primary}`}>
                {(violations || []).filter((v: any) => v.severity === 'high').length}
              </p>
            </div>
            <AlertTriangle className="h-8 w-8 text-orange-500" />
          </div>
        </div>
        <div className={`${theme.bg.card} rounded-lg shadow-sm p-4 border-l-4 border-yellow-500`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme.text.secondary}`}>Medium</p>
              <p className={`text-2xl font-bold ${theme.text.primary}`}>
                {(violations || []).filter((v: any) => v.severity === 'medium').length}
              </p>
            </div>
            <AlertTriangle className="h-8 w-8 text-yellow-500" />
          </div>
        </div>
        <div className={`${theme.bg.card} rounded-lg shadow-sm p-4 border-l-4 border-blue-500`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme.text.secondary}`}>Low</p>
              <p className={`text-2xl font-bold ${theme.text.primary}`}>
                {(violations || []).filter((v: any) => v.severity === 'low').length}
              </p>
            </div>
            <AlertTriangle className="h-8 w-8 text-blue-500" />
          </div>
        </div>
      </div>

      {/* Incidents List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* List View */}
        <div className="lg:col-span-2 space-y-4">
          {filteredViolations.map((violation: any, index: number) => (
            <div
              key={index}
              onClick={() => setSelectedViolation(violation)}
              className={`${theme.bg.card} rounded-xl shadow-sm p-6 hover:shadow-md transition-all cursor-pointer ${
                selectedViolation?.control_id === violation.control_id ? 'ring-2 ring-blue-500' : ''
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4 flex-1">
                  <div className={`w-3 h-3 rounded-full mt-1 ${getSeverityColor(violation.severity)}`} />
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2 flex-wrap">
                      <h3 className={`font-semibold ${theme.text.primary}`}>{violation.control_id}</h3>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getSeverityBadgeColor(violation.severity)}`}>
                        {violation.severity.toUpperCase()}
                      </span>
                      {violation.category && (
                        <span className={`px-2 py-1 ${theme.bg.tertiary} ${theme.text.secondary} rounded-full text-xs`}>
                          {violation.category}
                        </span>
                      )}
                      {violationPRs[violation.id]?.length > 0 && (
                        <span className="flex items-center gap-1 px-2 py-1 bg-orange-100 text-orange-700 rounded-full text-xs font-medium">
                          <GitPullRequest className="h-3 w-3" />
                          {violationPRs[violation.id].length} PR{violationPRs[violation.id].length > 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                    <p className={`text-sm ${theme.text.secondary} mb-2`}>{violation.description}</p>
                    <div className={`flex items-center gap-4 text-xs ${theme.text.tertiary}`}>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {violation.timestamp ? new Date(violation.timestamp).toLocaleString() : 'N/A'}
                      </span>
                      {violation.resource && (
                        <span className="flex items-center gap-1">
                          <FileText className="h-3 w-3" />
                          {violation.resource}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <ArrowRight className={`h-5 w-5 ${theme.text.muted}`} />
              </div>
            </div>
          ))}
          {filteredViolations.length === 0 && (
            <div className={`${theme.bg.card} rounded-xl shadow-sm p-12 text-center`}>
              <CheckCircle className="h-16 w-16 mx-auto mb-4 text-green-500" />
              <h3 className={`text-lg font-medium ${theme.text.primary} mb-2`}>No incidents found</h3>
              <p className={`${theme.text.secondary}`}>
                {searchTerm || selectedSeverity !== 'all' || selectedCategory !== 'all'
                  ? 'Try adjusting your filters'
                  : 'Great job! No security incidents detected'}
              </p>
            </div>
          )}
        </div>

        {/* Detail View */}
        <div className="lg:col-span-1">
          {selectedViolation ? (
            <div className={`${theme.bg.card} rounded-xl shadow-sm p-6 sticky top-6`}>
              <div className="flex items-center justify-between mb-4">
                <h3 className={`text-lg font-semibold ${theme.text.primary}`}>Incident Details</h3>
                <button
                  onClick={() => setSelectedViolation(null)}
                  className={`p-1 hover:${theme.bg.tertiary} rounded`}
                >
                  <XCircle className={`h-5 w-5 ${theme.text.muted}`} />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className={`text-xs font-medium ${theme.text.tertiary} uppercase`}>Control ID</label>
                  <p className={`text-sm font-medium ${theme.text.primary} mt-1`}>{selectedViolation.control_id}</p>
                </div>

                <div>
                  <label className={`text-xs font-medium ${theme.text.tertiary} uppercase`}>Severity</label>
                  <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium border mt-1 ${getSeverityBadgeColor(selectedViolation.severity)}`}>
                    {selectedViolation.severity.toUpperCase()}
                  </span>
                </div>

                <div>
                  <label className={`text-xs font-medium ${theme.text.tertiary} uppercase`}>Category</label>
                  <p className={`text-sm ${theme.text.primary} mt-1`}>{selectedViolation.category || 'N/A'}</p>
                </div>

                <div>
                  <label className={`text-xs font-medium ${theme.text.tertiary} uppercase`}>Description</label>
                  <p className={`text-sm ${theme.text.secondary} mt-1`}>{selectedViolation.description}</p>
                </div>

                {selectedViolation.resource && (
                  <div>
                    <label className={`text-xs font-medium ${theme.text.tertiary} uppercase`}>Affected Resource</label>
                    <p className={`text-sm ${theme.text.primary} mt-1 font-mono ${theme.bg.secondary} p-2 rounded`}>
                      {selectedViolation.resource}
                    </p>
                  </div>
                )}

                {selectedViolation.root_cause && (
                  <div className="bg-orange-50 border-l-4 border-orange-500 p-4 rounded">
                    <label className="text-xs font-medium text-orange-900 uppercase">Root Cause Analysis</label>
                    <p className="text-sm text-orange-800 mt-2">{selectedViolation.root_cause}</p>
                  </div>
                )}

                {selectedViolation.remediation && (
                  <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                    <label className="text-xs font-medium text-blue-900 uppercase">Remediation Steps</label>
                    <p className="text-sm text-blue-800 mt-2">{selectedViolation.remediation}</p>
                  </div>
                )}

                <div>
                  <label className={`text-xs font-medium ${theme.text.tertiary} uppercase`}>Detected At</label>
                  <p className={`text-sm ${theme.text.primary} mt-1`}>
                    {selectedViolation.timestamp ? new Date(selectedViolation.timestamp).toLocaleString() : 'N/A'}
                  </p>
                </div>

                {violationPRs[selectedViolation.id]?.length > 0 && (
                  <div className="bg-orange-50 border-l-4 border-orange-500 p-4 rounded">
                    <label className="text-xs font-medium text-orange-900 uppercase flex items-center gap-2 mb-3">
                      <GitPullRequest className="h-4 w-4" />
                      Linked Pull Requests ({violationPRs[selectedViolation.id].length})
                    </label>
                    <div className="space-y-2">
                      {violationPRs[selectedViolation.id].map((pr: any) => (
                        <div key={pr.id} className={`${theme.bg.card} p-3 rounded border border-orange-200`}>
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className={`text-sm font-medium ${theme.text.primary} truncate`}>
                                  #{pr.number}
                                </span>
                                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                  pr.status === 'merged'
                                    ? 'bg-orange-100 text-orange-700'
                                    : pr.status === 'open'
                                    ? 'bg-green-100 text-green-700'
                                    : `${theme.bg.tertiary} ${theme.text.secondary}`
                                }`}>
                                  {pr.status}
                                </span>
                              </div>
                              <p className={`text-xs ${theme.text.secondary} line-clamp-2`}>{pr.title}</p>
                            </div>
                            <a
                              href={pr.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex-shrink-0 p-1 hover:bg-orange-100 rounded"
                              title="View on GitHub"
                            >
                              <ExternalLink className="h-4 w-4 text-orange-600" />
                            </a>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className={`pt-4 border-t ${theme.border.primary}`}>
                  <button className="w-full px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors font-medium">
                    Mark as Resolved
                  </button>
                  <button className={`w-full mt-2 px-4 py-2 ${theme.bg.tertiary} ${theme.text.secondary} rounded-lg hover:bg-gray-200 transition-colors font-medium`}>
                    Generate Report
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className={`${theme.bg.card} rounded-xl shadow-sm p-12 text-center sticky top-6`}>
              <AlertTriangle className="h-16 w-16 mx-auto mb-4 text-gray-300" />
              <h3 className={`text-lg font-medium ${theme.text.primary} mb-2`}>No Incident Selected</h3>
              <p className={`text-sm ${theme.text.secondary}`}>
                Click on an incident to view details and remediation steps
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Made with Bob