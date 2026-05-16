import React, { useState, useEffect } from 'react';
import { FileText, Download, Calendar, Filter, Loader2, Trash2, Eye } from 'lucide-react';
import { theme } from '@/config/theme';
import { useToast, ToastContainer } from '@/components/ToastNotification';

interface Report {
  id: string;
  name: string;
  type: string;
  standard: string | null;
  format: string;
  generated_at: string;
  status: string;
  size_bytes: number;
}

export const AuditorReports: React.FC = () => {
  const { toasts, removeToast, showSuccess, showWarning } = useToast();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [filterStandard, setFilterStandard] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [error, setError] = useState<string | null>(null);

  // Available standards
  const standards = ['SOC2', 'HIPAA', 'PCI-DSS', 'ISO27001', 'GDPR'];

  useEffect(() => {
    fetchReports();
  }, [filterStandard, filterStatus]);

  const fetchReports = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (filterStandard !== 'all') params.append('standard', filterStandard);
      if (filterStatus !== 'all') params.append('status', filterStatus);
      
      const response = await fetch(`http://localhost:8000/reports?${params.toString()}`);
      if (response.ok) {
        const data = await response.json();
        setReports(data.reports || []);
      } else {
        setError('Failed to fetch reports');
      }
    } catch (err) {
      console.error('Error fetching reports:', err);
      setError('Failed to fetch reports');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async (format: string = 'json') => {
    setGenerating(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/reports/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          report_type: 'compliance',
          standard: filterStandard !== 'all' ? filterStandard : null,
          format: format
        })
      });

      if (response.ok) {
        const data = await response.json();
        showSuccess('Report Generated', `Report generated successfully: ${data.report.name}`);
        fetchReports(); // Refresh list
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to generate report');
      }
    } catch (err) {
      console.error('Error generating report:', err);
      setError('Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadReport = async (reportId: string, fileName: string) => {
    try {
      const response = await fetch(`http://localhost:8000/reports/${reportId}/download`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else {
        showWarning('Download Failed', 'Failed to download report');
      }
    } catch (err) {
      console.error('Error downloading report:', err);
      showWarning('Download Failed', 'Failed to download report');
    }
  };

  const handleDeleteReport = async (reportId: string) => {
    if (!confirm('Are you sure you want to delete this report?')) return;

    try {
      const response = await fetch(`http://localhost:8000/reports/${reportId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        showSuccess('Report Deleted', 'Report deleted successfully');
        fetchReports(); // Refresh list
      } else {
        showWarning('Delete Failed', 'Failed to delete report');
      }
    } catch (err) {
      console.error('Error deleting report:', err);
      showWarning('Delete Failed', 'Failed to delete report');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <>
      <ToastContainer toasts={toasts} onClose={removeToast} />
      <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className={`text-3xl font-bold ${theme.text.primary}`}>Audit Reports</h1>
          <p className={`${theme.text.secondary} mt-1`}>Generate and download compliance audit reports</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => handleGenerateReport('json')}
            disabled={generating}
            className="flex items-center gap-2 px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {generating ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <FileText className="h-5 w-5" />
                Generate JSON Report
              </>
            )}
          </button>
          <button
            onClick={() => handleGenerateReport('csv')}
            disabled={generating}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {generating ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <FileText className="h-5 w-5" />
                Generate CSV Report
              </>
            )}
          </button>
          <button
            onClick={() => handleGenerateReport('html')}
            disabled={generating}
            className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {generating ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <FileText className="h-5 w-5" />
                Generate HTML Report
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className={`${theme.bg.card} rounded-xl shadow-sm p-4`}>
        <div className="flex gap-4 items-center">
          <Filter className={`h-5 w-5 ${theme.text.tertiary}`} />
          <select
            value={filterStandard}
            onChange={(e) => setFilterStandard(e.target.value)}
            className={`px-4 py-2 border ${theme.border.secondary} rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
          >
            <option value="all">All Standards</option>
            {standards.map(std => (
              <option key={std} value={std}>{std}</option>
            ))}
          </select>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className={`px-4 py-2 border ${theme.border.secondary} rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
          >
            <option value="all">All Status</option>
            <option value="completed">Completed</option>
            <option value="in_progress">In Progress</option>
            <option value="draft">Draft</option>
          </select>
          <button
            onClick={fetchReports}
            disabled={loading}
            className={`ml-auto px-4 py-2 ${theme.bg.tertiary} ${theme.text.secondary} rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors`}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Reports List */}
      <div className={`${theme.bg.card} rounded-xl shadow-sm overflow-hidden`}>
        {loading && reports.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
            <span className={`ml-2 ${theme.text.secondary}`}>Loading reports...</span>
          </div>
        ) : reports.length === 0 ? (
          <div className={`text-center py-12 ${theme.text.tertiary}`}>
            <FileText className={`h-12 w-12 mx-auto mb-4 ${theme.text.muted}`} />
            <p>No reports found. Generate your first report above.</p>
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className={`${theme.bg.secondary}`}>
              <tr>
                <th className={`px-6 py-3 text-left text-xs font-medium ${theme.text.tertiary} uppercase`}>Report Name</th>
                <th className={`px-6 py-3 text-left text-xs font-medium ${theme.text.tertiary} uppercase`}>Standard</th>
                <th className={`px-6 py-3 text-left text-xs font-medium ${theme.text.tertiary} uppercase`}>Format</th>
                <th className={`px-6 py-3 text-left text-xs font-medium ${theme.text.tertiary} uppercase`}>Size</th>
                <th className={`px-6 py-3 text-left text-xs font-medium ${theme.text.tertiary} uppercase`}>Date</th>
                <th className={`px-6 py-3 text-left text-xs font-medium ${theme.text.tertiary} uppercase`}>Status</th>
                <th className={`px-6 py-3 text-right text-xs font-medium ${theme.text.tertiary} uppercase`}>Actions</th>
              </tr>
            </thead>
            <tbody className={`${theme.bg.card} divide-y divide-gray-200`}>
              {reports.map((report) => (
                <tr key={report.id} className={`hover:${theme.bg.secondary}`}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <FileText className={`h-5 w-5 ${theme.text.muted} mr-3`} />
                      <span className={`font-medium ${theme.text.primary}`}>{report.name}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 bg-blue-100 text-cyan-400 rounded-full text-xs font-medium">
                      {report.standard || 'All Standards'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`text-sm ${theme.text.secondary} uppercase`}>{report.format}</span>
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm ${theme.text.tertiary}`}>
                    {formatFileSize(report.size_bytes)}
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm ${theme.text.tertiary}`}>
                    {new Date(report.generated_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      report.status === 'completed' ? 'bg-green-100 text-green-700' :
                      report.status === 'in_progress' ? 'bg-yellow-100 text-yellow-700' :
                      `${theme.bg.tertiary} ${theme.text.secondary}`
                    }`}>
                      {report.status === 'completed' ? 'Completed' :
                       report.status === 'in_progress' ? 'In Progress' : 'Draft'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => handleDownloadReport(report.id, `${report.id}.${report.format}`)}
                      className="text-green-600 hover:text-green-900 inline-flex items-center gap-1 mr-3"
                      title="Download"
                    >
                      <Download className="h-4 w-4" />
                      Download
                    </button>
                    <button
                      onClick={() => handleDeleteReport(report.id)}
                      className="text-red-600 hover:text-red-900 inline-flex items-center gap-1"
                      title="Delete"
                    >
                      <Trash2 className="h-4 w-4" />
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Report Templates */}
      <div className={`${theme.bg.card} rounded-xl shadow-sm p-6`}>
        <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4`}>Quick Report Templates</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { name: 'SOC2 Type II', standard: 'SOC2', format: 'html' },
            { name: 'HIPAA Security Rule', standard: 'HIPAA', format: 'html' },
            { name: 'PCI-DSS v4.0', standard: 'PCI-DSS', format: 'html' }
          ].map((template) => (
            <div
              key={template.name}
              onClick={() => {
                setFilterStandard(template.standard);
                handleGenerateReport(template.format);
              }}
              className={`border ${theme.border.primary} rounded-lg p-4 hover:border-blue-500 hover:shadow-md transition-all cursor-pointer`}
            >
              <FileText className="h-8 w-8 text-cyan-400 mb-2" />
              <h4 className={`font-medium ${theme.text.primary} mb-1`}>{template.name}</h4>
              <p className={`text-sm ${theme.text.secondary}`}>Standard compliance report template</p>
              <p className={`text-xs ${theme.text.tertiary} mt-2`}>Format: {template.format.toUpperCase()}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
    </>
  );
};

// Made with Bob
