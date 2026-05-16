import React, { useEffect, useState } from 'react';
import { FileText, Search, Upload, RefreshCw, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react';
import { useComplianceStore } from '../../store/useComplianceStore';
import { theme } from '@/config/theme';
import { useToast, ToastContainer } from '@/components/ToastNotification';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

interface Control {
  id: string;
  control_id?: string;
  standard: string;
  description: string;
  category?: string;
  severity?: string;
  title?: string;
}

interface PDFFile {
  filename: string;
  size_bytes: number;
  modified_time: string;
}

export const AdminControls: React.FC = () => {
  const { complianceScore } = useComplianceStore();
  const { toasts, removeToast, showSuccess, showWarning } = useToast();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStandard, setSelectedStandard] = useState('all');
  const [controls, setControls] = useState<Control[]>([]);
  const [pdfs, setPdfs] = useState<PDFFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  const standards = Object.keys((complianceScore as any)?.standards || {});

  // Fetch controls from backend
  const fetchControls = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/controls`);
      if (response.ok) {
        const data = await response.json();
        setControls(data.controls || []);
        // Clear any previous error messages on success
        setMessage(null);
      } else {
        // Only show error for client errors (4xx), not server errors (5xx) during startup
        setControls([]);
        if (response.status >= 400 && response.status < 500) {
          setMessage({ type: 'error', text: 'Failed to fetch controls from server' });
        }
        // Silently ignore 5xx errors (backend might be starting up)
      }
    } catch (error) {
      console.error('Error fetching controls:', error);
      // Silently handle network errors - backend might be starting up
      setControls([]);
    } finally {
      setLoading(false);
    }
  };

  // Fetch stored PDFs
  const fetchPDFs = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/pdfs`);
      if (response.ok) {
        const data = await response.json();
        setPdfs(data.files || []);
      }
    } catch (error) {
      console.error('Error fetching PDFs:', error);
    }
  };

  // Upload PDF
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      setMessage(null);

      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        const successMessage = `Successfully uploaded ${file.name} - Extracted ${data.controls_count} controls`;
        setMessage({
          type: 'success',
          text: successMessage
        });
        showSuccess('New Skills Added', successMessage);
        await fetchControls();
        await fetchPDFs();
      } else {
        const error = await response.json();
        const errorMessage = error.detail || 'Upload failed';
        setMessage({ type: 'error', text: errorMessage });
        showWarning('Upload Failed', errorMessage);
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      setMessage({ type: 'error', text: 'Failed to upload PDF' });
      showWarning('Upload Failed', 'Failed to upload PDF');
    } finally {
      setUploading(false);
      // Reset file input
      event.target.value = '';
    }
  };

  // Re-ingest all PDFs
  const handleReingest = async () => {
    try {
      setIngesting(true);
      setMessage(null);

      const response = await fetch(`${API_BASE_URL}/ingest`, {
        method: 'POST',
      });

      if (response.ok) {
        const data = await response.json();
        const successMessage = `Re-ingested ${data.files_processed} PDFs - ${data.total_controls} controls`;
        setMessage({
          type: 'success',
          text: successMessage
        });
        showSuccess('Skills Updated', successMessage);
        await fetchControls();
      } else {
        const error = await response.json();
        const errorMessage = error.detail || 'Re-ingestion failed';
        setMessage({ type: 'error', text: errorMessage });
        showWarning('Re-ingestion Failed', errorMessage);
      }
    } catch (error) {
      console.error('Error re-ingesting:', error);
      setMessage({ type: 'error', text: 'Failed to re-ingest PDFs' });
      showWarning('Re-ingestion Failed', 'Failed to re-ingest PDFs');
    } finally {
      setIngesting(false);
    }
  };

  useEffect(() => {
    fetchControls();
    fetchPDFs();
  }, []);

  const filteredControls = (controls || []).filter(control => {
    const controlId = control.control_id || control.id || '';
    const description = control.description || control.title || '';
    const matchesSearch = description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         controlId.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStandard = selectedStandard === 'all' || control.standard === selectedStandard;
    return matchesSearch && matchesStandard;
  });

  // Pagination calculations
  const totalPages = Math.ceil(filteredControls.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedControls = filteredControls.slice(startIndex, endIndex);

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, selectedStandard]);

  return (
    <>
      <ToastContainer toasts={toasts} onClose={removeToast} />
      <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className={`text-3xl font-bold ${theme.text.primary}`}>Compliance Controls</h1>
          <p className={`${theme.text.secondary} mt-1`}>Manage and configure compliance controls</p>
        </div>
        <div className="flex gap-3">
          <label className="flex items-center gap-2 px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors cursor-pointer">
            <Upload className="h-5 w-5" />
            {uploading ? 'Uploading...' : 'Upload PDF'}
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
            />
          </label>
          <button 
            onClick={handleReingest}
            disabled={ingesting || pdfs.length === 0}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`h-5 w-5 ${ingesting ? 'animate-spin' : ''}`} />
            {ingesting ? 'Re-ingesting...' : 'Re-ingest All'}
          </button>
        </div>
      </div>

      {/* Message Banner */}
      {message && (
        <div className={`p-4 rounded-lg flex items-center gap-3 ${
          message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
        }`}>
          <AlertCircle className="h-5 w-5" />
          <span>{message.text}</span>
          <button 
            onClick={() => setMessage(null)}
            className="ml-auto text-sm underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Stats - Moved to Top */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-white/5">
          <div className="text-sm text-gray-400 font-medium">Total Controls</div>
          <div className="text-3xl font-bold text-white mt-2">{controls.length}</div>
        </div>
        <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-white/5">
          <div className="text-sm text-gray-400 font-medium">Stored PDFs</div>
          <div className="text-3xl font-bold text-white mt-2">{pdfs.length}</div>
        </div>
        <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-white/5">
          <div className="text-sm text-gray-400 font-medium">Standards</div>
          <div className="text-3xl font-bold text-white mt-2">{standards.length}</div>
        </div>
      </div>

      {/* Filters - Themed Search Bar */}
      <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-sm rounded-xl shadow-lg p-4 border border-white/5">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-orange-400" />
            <input
              type="text"
              placeholder="Search controls..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
            />
          </div>
          <select
            value={selectedStandard}
            onChange={(e) => setSelectedStandard(e.target.value)}
            className="px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
          >
            <option value="all">All Standards</option>
            {standards.map(std => (
              <option key={std} value={std}>{std}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Controls Table - Modern Design */}
      <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-sm rounded-2xl shadow-2xl overflow-hidden border border-white/5">
        {loading ? (
          <div className={`p-8 text-center ${theme.text.tertiary}`}>
            <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2" />
            Loading controls...
          </div>
        ) : filteredControls.length === 0 ? (
          <div className={`p-8 text-center ${theme.text.tertiary}`}>
            <FileText className={`h-12 w-12 mx-auto mb-3 ${theme.text.muted}`} />
            <p className="text-lg font-medium mb-2">No controls found</p>
            <p className="text-sm">Upload a compliance PDF to get started</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-white/5">
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Control ID</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Standard</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Description</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Category</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Severity</th>
                </tr>
              </thead>
              <tbody>
                {paginatedControls.map((control, index) => (
                  <tr
                    key={control.control_id || control.id || index}
                    className="border-b border-white/5 hover:bg-white/5 transition-colors duration-150"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-semibold text-white">
                        {control.control_id || control.id || 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gradient-to-r from-orange-500/20 to-amber-500/20 text-orange-400 border border-orange-500/30">
                        {control.standard || 'Unknown'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-300 line-clamp-2">
                        {control.description || control.title || 'No description'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-400">
                        {control.category || 'General'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
                        control.severity === 'critical' || control.severity === 'Critical'
                          ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                        control.severity === 'high' || control.severity === 'High'
                          ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                        control.severity === 'medium' || control.severity === 'Medium'
                          ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                        'bg-gray-500/20 text-gray-400 border border-gray-500/30'
                      }`}>
                        {control.severity || 'N/A'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {!loading && filteredControls.length > 0 && (
          <div className="px-6 py-4 border-t border-white/5 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-400">
                Showing {startIndex + 1} to {Math.min(endIndex, filteredControls.length)} of {filteredControls.length} controls
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
      </div>
    </>
  );
};