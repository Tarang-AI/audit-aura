import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Filter,
  RefreshCw,
  Search,
  XCircle,
  TrendingUp,
  Shield,
  FileText,
  Eye,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { theme } from '@/config/theme';

interface Violation {
  control_id: string;
  standard: string;
  category: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  description?: string;
  timestamp: string;
  last_seen?: string;
  occurrence_count?: number;
  resolved: boolean;
  resolved_at?: string;
  resource_identifier?: string;
  event: {
    source?: string;
    event_name?: string;
    resource_name?: string;
    resource_type?: string;
  };
}

interface ViolationStats {
  total: number;
  by_severity: Record<string, number>;
  by_standard: Record<string, number>;
  by_category: Record<string, number>;
  resolved: number;
  unresolved: number;
}

const severityColors = {
  critical: 'bg-red-100 text-red-800 border-red-200',
  high: 'bg-orange-100 text-orange-800 border-orange-200',
  medium: 'bg-amber-100 text-amber-800 border-amber-200',
  low: 'bg-blue-100 text-blue-800 border-blue-200',
};

const severityIcons = {
  critical: <AlertTriangle className="h-4 w-4" />,
  high: <AlertTriangle className="h-4 w-4" />,
  medium: <AlertTriangle className="h-4 w-4" />,
  low: <AlertTriangle className="h-4 w-4" />,
};

export const AdminViolations: React.FC = () => {
  const [violations, setViolations] = useState<Violation[]>([]);
  const [stats, setStats] = useState<ViolationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [selectedStandard, setSelectedStandard] = useState<string>('all');
  const [showResolved, setShowResolved] = useState(false);
  const [selectedViolation, setSelectedViolation] = useState<Violation | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  const fetchViolations = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (selectedSeverity !== 'all') params.append('severity', selectedSeverity);
      if (!showResolved) params.append('status', 'unresolved');
      params.append('include_resolved', showResolved.toString());

      const response = await fetch(`http://localhost:8000/violations/details?${params}`);
      if (response.ok) {
        const data = await response.json();
        setViolations(data.violations || []);
        setStats(data.stats || null);
      }
    } catch (error) {
      console.error('Failed to fetch violations:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchViolations();
    const interval = setInterval(fetchViolations, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [selectedSeverity, showResolved]);

  const filteredViolations = violations.filter((v) => {
    const matchesSearch =
      v.control_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      v.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      v.category?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      v.resource_identifier?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStandard = selectedStandard === 'all' || v.standard === selectedStandard;
    return matchesSearch && matchesStandard;
  });

  // Pagination calculations
  const totalPages = Math.ceil(filteredViolations.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedViolations = filteredViolations.slice(startIndex, endIndex);

  const standards = stats ? Object.keys(stats.by_standard) : [];

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, selectedSeverity, selectedStandard, showResolved]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Violations Management</h1>
          <p className="mt-1 text-gray-300">
            Monitor and manage compliance violations across all standards
          </p>
        </div>
        <button
          onClick={fetchViolations}
          disabled={loading}
          className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-orange-500 to-amber-500 px-4 py-2 text-sm font-medium text-white hover:from-orange-600 hover:to-amber-600 disabled:opacity-50 transition-all"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Stats Cards - Themed Design */}
      {stats && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-white/5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">Total Violations</p>
                <p className="mt-2 text-3xl font-bold text-white">{stats.total}</p>
              </div>
              <Shield className="h-8 w-8 text-gray-400" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-red-500/30">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-red-400">Unresolved</p>
                <p className="mt-2 text-3xl font-bold text-red-400">{stats.unresolved}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-400" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-green-500/30">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-400">Resolved</p>
                <p className="mt-2 text-3xl font-bold text-green-400">{stats.resolved}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-400" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-orange-500/30">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-400">Critical</p>
                <p className="mt-2 text-3xl font-bold text-orange-400">
                  {stats.by_severity.critical || 0}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-orange-400" />
            </div>
          </div>
        </div>
      )}

      {/* Filters - Themed Search Bar */}
      <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-sm rounded-xl shadow-lg p-4 border border-white/5">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label className="block text-sm font-semibold text-gray-400 mb-2">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-orange-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search violations..."
                className="w-full rounded-lg bg-gray-800/50 border border-gray-700/50 py-2.5 pl-10 pr-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-400 mb-2">Severity</label>
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="w-full rounded-lg bg-gray-800/50 border border-gray-700/50 py-2.5 px-3 text-white focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
            >
              <option value="all" className="bg-gray-800">All Severities</option>
              <option value="critical" className="bg-gray-800">Critical</option>
              <option value="high" className="bg-gray-800">High</option>
              <option value="medium" className="bg-gray-800">Medium</option>
              <option value="low" className="bg-gray-800">Low</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-400 mb-2">Standard</label>
            <select
              value={selectedStandard}
              onChange={(e) => setSelectedStandard(e.target.value)}
              className="w-full rounded-lg bg-gray-800/50 border border-gray-700/50 py-2.5 px-3 text-white focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
            >
              <option value="all" className="bg-gray-800">All Standards</option>
              {standards.map((std) => (
                <option key={std} value={std} className="bg-gray-800">
                  {std}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-400 mb-2">Status</label>
            <div className="flex items-center mt-3">
              <input
                type="checkbox"
                checked={showResolved}
                onChange={(e) => setShowResolved(e.target.checked)}
                className="h-4 w-4 rounded border-gray-600 text-orange-500 focus:ring-orange-500 bg-gray-800"
              />
              <span className="ml-2 text-sm text-gray-300">Show resolved</span>
            </div>
          </div>
        </div>
      </div>

      {/* Violations Table - Modern Design */}
      <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-sm rounded-2xl shadow-2xl overflow-hidden border border-white/5">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Control ID
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-600">
                  Standard
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-600">
                  Severity
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-600">
                  Resource
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-600">
                  Occurrences
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-600">
                  First Seen
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-600">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-600">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {loading ? (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center text-sm text-slate-500">
                    Loading violations...
                  </td>
                </tr>
              ) : paginatedViolations.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center text-sm text-slate-500">
                    No violations found
                  </td>
                </tr>
              ) : (
                paginatedViolations.map((violation, index) => (
                  <tr key={index} className="hover:bg-slate-50">
                    <td className="px-4 py-3 text-sm font-medium text-slate-900">
                      {violation.control_id}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-700 max-w-md">
                      <div className="line-clamp-2" title={violation.description}>
                        {violation.description || 'No description available'}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600">{violation.standard}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${
                          severityColors[violation.severity]
                        }`}
                      >
                        {severityIcons[violation.severity]}
                        {violation.severity}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600">
                      {violation.resource_identifier || violation.event?.resource_name || 'N/A'}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600">
                      {violation.occurrence_count || 1}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600">
                      {new Date(violation.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      {violation.resolved ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                          <CheckCircle className="h-3 w-3" />
                          Resolved
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800">
                          <XCircle className="h-3 w-3" />
                          Active
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => setSelectedViolation(violation)}
                        className="text-blue-600 hover:text-blue-800"
                        title="View details"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {!loading && filteredViolations.length > 0 && (
          <div className="px-6 py-4 border-t border-white/5 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-400">
                Showing {startIndex + 1} to {Math.min(endIndex, filteredViolations.length)} of {filteredViolations.length} violations
              </span>
              <select
                value={itemsPerPage}
                onChange={(e) => {
                  setItemsPerPage(Number(e.target.value));
                  setCurrentPage(1);
                }}
                className="px-3 py-1.5 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
              >
                <option value={10}>10 per page</option>
                <option value={25}>25 per page</option>
                <option value={50}>50 per page</option>
                <option value={100}>100 per page</option>
              </select>
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="p-2 rounded-lg bg-gray-800/50 border border-gray-700/50 text-white hover:bg-gray-700/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
              
              <div className="flex items-center gap-1">
                {Array.from({ length: totalPages }, (_, i) => i + 1)
                  .filter(page => {
                    if (totalPages <= 7) return true;
                    if (page === 1 || page === totalPages) return true;
                    if (page >= currentPage - 1 && page <= currentPage + 1) return true;
                    return false;
                  })
                  .map((page, index, array) => (
                    <React.Fragment key={page}>
                      {index > 0 && array[index - 1] !== page - 1 && (
                        <span className="px-2 text-gray-500">...</span>
                      )}
                      <button
                        onClick={() => setCurrentPage(page)}
                        className={`min-w-[40px] px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                          currentPage === page
                            ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-lg'
                            : 'bg-gray-800/50 border border-gray-700/50 text-gray-300 hover:bg-gray-700/50'
                        }`}
                      >
                        {page}
                      </button>
                    </React.Fragment>
                  ))}
              </div>
              
              <button
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
                className="p-2 rounded-lg bg-gray-800/50 border border-gray-700/50 text-white hover:bg-gray-700/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                <ChevronRight className="h-5 w-5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Violation Detail Modal */}
      {selectedViolation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6 shadow-xl">
            <div className="mb-4 flex items-start justify-between">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Violation Details</h2>
                <p className="mt-1 text-sm text-slate-600">{selectedViolation.control_id}</p>
              </div>
              <button
                onClick={() => setSelectedViolation(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <XCircle className="h-6 w-6" />
              </button>
            </div>

            <div className="space-y-4">
              {selectedViolation.description && (
                <div>
                  <h3 className="text-sm font-medium text-slate-700">Description</h3>
                  <p className="mt-1 text-sm text-slate-900">{selectedViolation.description}</p>
                </div>
              )}

              <div>
                <h3 className="text-sm font-medium text-slate-700">Standard</h3>
                <p className="mt-1 text-sm text-slate-900">{selectedViolation.standard}</p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-slate-700">Category</h3>
                <p className="mt-1 text-sm text-slate-900">{selectedViolation.category}</p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-slate-700">Severity</h3>
                <span
                  className={`mt-1 inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${
                    severityColors[selectedViolation.severity]
                  }`}
                >
                  {severityIcons[selectedViolation.severity]}
                  {selectedViolation.severity}
                </span>
              </div>

              <div>
                <h3 className="text-sm font-medium text-slate-700">Resource</h3>
                <p className="mt-1 text-sm text-slate-900">
                  {selectedViolation.resource_identifier || 'N/A'}
                </p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-slate-700">Event Details</h3>
                <div className="mt-1 rounded-lg bg-slate-50 p-3">
                  <pre className="text-xs text-slate-700">
                    {JSON.stringify(selectedViolation.event, null, 2)}
                  </pre>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="text-sm font-medium text-slate-700">First Seen</h3>
                  <p className="mt-1 text-sm text-slate-900">
                    {new Date(selectedViolation.timestamp).toLocaleString()}
                  </p>
                </div>
                {selectedViolation.last_seen && (
                  <div>
                    <h3 className="text-sm font-medium text-slate-700">Last Seen</h3>
                    <p className="mt-1 text-sm text-slate-900">
                      {new Date(selectedViolation.last_seen).toLocaleString()}
                    </p>
                  </div>
                )}
              </div>

              <div>
                <h3 className="text-sm font-medium text-slate-700">Occurrences</h3>
                <p className="mt-1 text-sm text-slate-900">
                  {selectedViolation.occurrence_count || 1}
                </p>
              </div>

              {selectedViolation.resolved && (
                <div>
                  <h3 className="text-sm font-medium text-slate-700">Resolved At</h3>
                  <p className="mt-1 text-sm text-slate-900">
                    {selectedViolation.resolved_at
                      ? new Date(selectedViolation.resolved_at).toLocaleString()
                      : 'N/A'}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};