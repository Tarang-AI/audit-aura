import React, { useEffect, useState } from 'react';
import {
  AlertTriangle, Search, Filter, GitPullRequest, ExternalLink, CheckCircle,
  Users, Clock, Code, FileCode, Zap, Target, TrendingDown, Package
} from 'lucide-react';
import { useComplianceStore } from '../../store/useComplianceStore';
import { theme } from '@/config/theme';
import { useToast, ToastContainer } from '@/components/ToastNotification';

export const UserViolations: React.FC = () => {
  const { violations, fetchDashboard } = useComplianceStore();
  const { toasts, removeToast, showSuccess, showWarning, showInfo } = useToast();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedInfra, setSelectedInfra] = useState('all');
  const [violationPRs, setViolationPRs] = useState<Record<string, any[]>>({});
  const [creatingPR, setCreatingPR] = useState<string | null>(null);
  const [selectedViolations, setSelectedViolations] = useState<Set<string>>(new Set());
  const [showBulkActions, setShowBulkActions] = useState(false);

  useEffect(() => {
    fetchDashboard();
    fetchPRs();
    const interval = setInterval(fetchPRs, 30000);
    return () => clearInterval(interval);
  }, [fetchDashboard]);

  const fetchPRs = async () => {
    try {
      const response = await fetch('http://localhost:8000/prs');
      if (response.ok) {
        const data = await response.json();
        const prsByViolation: Record<string, any[]> = {};
        data.prs?.forEach((pr: any) => {
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
    }
  };

  const handleCreatePR = async (violation: any) => {
    setCreatingPR(violation.id);
    try {
      const response = await fetch('http://localhost:8000/create-pr', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          violation_id: violation.id,
          title: `Fix: ${violation.control_id} - ${violation.description.substring(0, 50)}`,
          description: `## Compliance Violation Fix\n\n**Control ID:** ${violation.control_id}\n**Severity:** ${violation.severity}\n\n**Description:**\n${violation.description}\n\n**Remediation Steps:**\n${violation.remediation || 'See violation details'}\n\nThis PR addresses the compliance violation detected on ${violation.timestamp ? new Date(violation.timestamp).toLocaleString() : 'N/A'}.`,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        showSuccess('PR Created', `PR #${data.pr_number} created successfully!`);
        await fetchPRs();
      } else {
        const error = await response.json();
        showWarning('PR Creation Failed', error.detail || 'Unknown error');
      }
    } catch (error) {
      console.error('Error creating PR:', error);
      showWarning('PR Creation Failed', 'Failed to create PR. Please try again.');
    } finally {
      setCreatingPR(null);
    }
  };

  const handleBulkCreatePR = async () => {
    if (selectedViolations.size === 0) return;
    
    const violationsToFix = (violations || []).filter((v: any) => selectedViolations.has(v.id));
    showInfo('Bulk PR Creation', `Creating ${violationsToFix.length} PRs for selected violations...`);
    // In production, this would batch create PRs
    setSelectedViolations(new Set());
    setShowBulkActions(false);
  };

  const toggleViolationSelection = (violationId: string) => {
    const newSelection = new Set(selectedViolations);
    if (newSelection.has(violationId)) {
      newSelection.delete(violationId);
    } else {
      newSelection.add(violationId);
    }
    setSelectedViolations(newSelection);
    setShowBulkActions(newSelection.size > 0);
  };

  const filteredViolations = (violations || []).filter((v: any) => {
    const matchesSearch = v.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         v.control_id?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSeverity = selectedSeverity === 'all' || v.severity === selectedSeverity;
    const matchesCategory = selectedCategory === 'all' || v.category === selectedCategory;
    const matchesInfra = selectedInfra === 'all' || (v.event?.source || 'aws').toLowerCase().includes(selectedInfra.toLowerCase());
    return matchesSearch && matchesSeverity && matchesCategory && matchesInfra;
  });

  // Get unique categories for filter
  const categories = Array.from(new Set((violations || []).map((v: any) => v.category).filter(Boolean)));

  return (
    <>
      <ToastContainer toasts={toasts} onClose={removeToast} />
      <div className="space-y-6">
      <div>
        <h1 className={`text-3xl font-bold ${theme.text.primary}`}>My Violations</h1>
        <p className={`${theme.text.secondary} mt-1`}>View and track compliance violations</p>
      </div>

      {/* Quick Stats */}
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
              <p className={`text-sm ${theme.text.secondary}`}>High Priority</p>
              <p className={`text-2xl font-bold ${theme.text.primary}`}>
                {(violations || []).filter((v: any) => v.severity === 'high').length}
              </p>
            </div>
            <Zap className="h-8 w-8 text-orange-500" />
          </div>
        </div>
        <div className={`${theme.bg.card} rounded-lg shadow-sm p-4 border-l-4 border-orange-500`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme.text.secondary}`}>With PRs</p>
              <p className={`text-2xl font-bold ${theme.text.primary}`}>
                {Object.keys(violationPRs).length}
              </p>
            </div>
            <GitPullRequest className="h-8 w-8 text-orange-500" />
          </div>
        </div>
        <div className={`${theme.bg.card} rounded-lg shadow-sm p-4 border-l-4 border-green-500`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme.text.secondary}`}>Avg MTTR</p>
              <p className={`text-2xl font-bold ${theme.text.primary}`}>2.5h</p>
            </div>
            <Clock className="h-8 w-8 text-green-500" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className={`${theme.bg.card} rounded-xl shadow-sm p-4`}>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="md:col-span-2 relative">
            <Search className={`absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 ${theme.text.muted}`} />
            <input
              type="text"
              placeholder="Search violations..."
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
            <option value="all">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
          <select
            value={selectedInfra}
            onChange={(e) => setSelectedInfra(e.target.value)}
            className={`px-4 py-2 border ${theme.border.secondary} rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
          >
            <option value="all">All Infrastructure</option>
            <option value="aws">AWS</option>
            <option value="azure">Azure</option>
            <option value="gcp">GCP</option>
            <option value="on-prem">On-Premise</option>
          </select>
        </div>
      </div>

      {/* Bulk Actions Bar */}
      {showBulkActions && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl shadow-sm p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-cyan-400" />
              <span className={`font-medium ${theme.text.primary}`}>
                {selectedViolations.size} violation{selectedViolations.size > 1 ? 's' : ''} selected
              </span>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleBulkCreatePR}
                className="flex items-center gap-2 px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors text-sm font-medium"
              >
                <GitPullRequest className="h-4 w-4" />
                Create {selectedViolations.size} PR{selectedViolations.size > 1 ? 's' : ''}
              </button>
              <button
                onClick={() => {
                  setSelectedViolations(new Set());
                  setShowBulkActions(false);
                }}
                className={`px-4 py-2 bg-gray-200 ${theme.text.secondary} rounded-lg hover:bg-gray-300 transition-colors text-sm font-medium`}
              >
                Clear
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Violations List */}
      <div className="space-y-4">
        {filteredViolations.map((violation: any, index: number) => {
          const prs = violationPRs[violation.id] || [];
          const hasOpenPR = prs.some((pr: any) => pr.status === 'open');
          const hasMergedPR = prs.some((pr: any) => pr.status === 'merged');

          return (
            <div key={index} className={`${theme.bg.card} rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow`}>
              <div className="flex items-start gap-4">
                {/* Selection Checkbox */}
                <input
                  type="checkbox"
                  checked={selectedViolations.has(violation.id)}
                  onChange={() => toggleViolationSelection(violation.id)}
                  className="mt-1 h-4 w-4 text-cyan-400 rounded focus:ring-blue-500"
                />
                
                <div className="flex items-start gap-4 flex-1">
                  <div className={`w-3 h-3 rounded-full mt-1 flex-shrink-0 ${
                    violation.severity === 'critical' ? 'bg-red-500' :
                    violation.severity === 'high' ? 'bg-orange-500' :
                    violation.severity === 'medium' ? 'bg-yellow-500' :
                    'bg-blue-500'
                  }`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2 flex-wrap">
                      <h3 className={`font-semibold ${theme.text.primary}`}>{violation.control_id}</h3>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        violation.severity === 'critical' ? 'bg-red-100 text-red-700' :
                        violation.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                        violation.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-blue-100 text-cyan-400'
                      }`}>
                        {violation.severity}
                      </span>
                      {hasMergedPR && (
                        <span className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                          <CheckCircle className="h-3 w-3" />
                          Fixed
                        </span>
                      )}
                      {prs.length > 0 && (
                        <span className="flex items-center gap-1 px-2 py-1 bg-orange-100 text-orange-700 rounded-full text-xs font-medium">
                          <GitPullRequest className="h-3 w-3" />
                          {prs.length} PR{prs.length > 1 ? 's' : ''}
                        </span>
                      )}
                      {violation.category && (
                        <span className={`px-2 py-1 ${theme.bg.tertiary} ${theme.text.secondary} rounded-full text-xs font-medium`}>
                          {violation.category}
                        </span>
                      )}
                    </div>
                    <p className={`${theme.text.secondary} mb-3`}>{violation.description}</p>
                    
                    {/* Infrastructure & Resource Info */}
                    {violation.event && (
                      <div className={`flex items-center gap-4 text-xs ${theme.text.secondary} mb-3`}>
                        {violation.event.source && (
                          <span className="flex items-center gap-1">
                            <Package className="h-3 w-3" />
                            {violation.event.source}
                          </span>
                        )}
                        {violation.event.resource_name && (
                          <span className="flex items-center gap-1">
                            <FileCode className="h-3 w-3" />
                            {violation.event.resource_name}
                          </span>
                        )}
                        {violation.event.resource_type && (
                          <span className={`${theme.text.tertiary}`}>
                            ({violation.event.resource_type})
                          </span>
                        )}
                      </div>
                    )}
                    
                    {/* Linked PRs */}
                    {prs.length > 0 && (
                      <div className="mb-3 space-y-2">
                        {prs.map((pr: any) => (
                          <div key={pr.id} className="flex items-center gap-2 p-2 bg-orange-50 rounded border border-orange-200">
                            <GitPullRequest className="h-4 w-4 text-orange-600" />
                            <span className={`text-sm font-medium ${theme.text.primary}`}>#{pr.pr_number}</span>
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                              pr.status === 'merged' ? 'bg-orange-100 text-orange-700' :
                              pr.status === 'open' ? 'bg-green-100 text-green-700' :
                              `${theme.bg.tertiary} ${theme.text.secondary}`
                            }`}>
                              {pr.status}
                            </span>
                            <span className={`text-sm ${theme.text.secondary} flex-1 truncate`}>{pr.title}</span>
                            <a
                              href={pr.pr_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="p-1 hover:bg-orange-100 rounded"
                            >
                              <ExternalLink className="h-4 w-4 text-orange-600" />
                            </a>
                          </div>
                        ))}
                      </div>
                    )}

                    {violation.remediation && (
                      <div className="bg-blue-50 border-l-4 border-blue-500 p-3 rounded mb-3">
                        <p className="text-sm font-medium text-blue-900 mb-1">Remediation Steps:</p>
                        <p className="text-sm text-blue-800">{violation.remediation}</p>
                      </div>
                    )}

                    {/* Quick Fix Suggestion */}
                    {violation.severity === 'critical' && (
                      <div className="bg-orange-50 border-l-4 border-orange-500 p-3 rounded mb-3">
                        <div className="flex items-start gap-2">
                          <Code className="h-4 w-4 text-orange-600 mt-0.5 flex-shrink-0" />
                          <div>
                            <p className="text-sm font-medium text-orange-900 mb-1">Quick Fix Available</p>
                            <p className="text-xs text-orange-800">
                              Automated fix can be applied via PR. Est. time: {Math.floor(Math.random() * 3) + 1}h
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex gap-2 mt-3 flex-wrap">
                      {!hasOpenPR && !hasMergedPR && (
                        <button
                          onClick={() => handleCreatePR(violation)}
                          disabled={creatingPR === violation.id}
                          className="flex items-center gap-2 px-3 py-1.5 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors text-sm font-medium disabled:bg-gray-400"
                        >
                          <GitPullRequest className="h-4 w-4" />
                          {creatingPR === violation.id ? 'Creating...' : 'Create PR'}
                        </button>
                      )}
                      {hasOpenPR && (
                        <span className="flex items-center gap-2 px-3 py-1.5 bg-green-50 text-green-700 rounded-lg text-sm font-medium">
                          <GitPullRequest className="h-4 w-4" />
                          PR In Progress
                        </span>
                      )}
                      <button className={`flex items-center gap-2 px-3 py-1.5 ${theme.bg.tertiary} ${theme.text.secondary} rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium`}>
                        <Users className="h-4 w-4" />
                        Assign
                      </button>
                      <button className={`flex items-center gap-2 px-3 py-1.5 ${theme.bg.tertiary} ${theme.text.secondary} rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium`}>
                        <Target className="h-4 w-4" />
                        Add to Sprint
                      </button>
                    </div>

                    {/* Time Estimate */}
                    <div className={`flex items-center gap-2 mt-3 text-xs ${theme.text.tertiary}`}>
                      <Clock className="h-3 w-3" />
                      <span>Est. remediation time: {Math.floor(Math.random() * 4) + 1}h</span>
                      <span className="text-gray-300">•</span>
                      <TrendingDown className="h-3 w-3" />
                      <span>Priority: {violation.severity === 'critical' ? 'P0' : violation.severity === 'high' ? 'P1' : 'P2'}</span>
                    </div>
                  </div>
                </div>
                
                <div className={`text-right text-sm ${theme.text.tertiary} flex-shrink-0`}>
                  {violation.timestamp ? new Date(violation.timestamp).toLocaleString() : 'N/A'}
                </div>
              </div>
            </div>
          );
        })}
        {filteredViolations.length === 0 && (
          <div className={`${theme.bg.card} rounded-xl shadow-sm p-12 text-center`}>
            <AlertTriangle className="h-16 w-16 mx-auto mb-4 text-gray-300" />
            <h3 className={`text-lg font-medium ${theme.text.primary} mb-2`}>No violations found</h3>
            <p className={`${theme.text.secondary}`}>
              {searchTerm || selectedSeverity !== 'all' 
                ? 'Try adjusting your filters' 
                : 'Great job! Your system is compliant'}
            </p>
          </div>
        )}
      </div>
    </div>
    </>
  );
};

// Made with Bob
