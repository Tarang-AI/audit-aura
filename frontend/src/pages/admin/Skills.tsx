import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { apiService } from '@/services/api';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { useToast, ToastContainer } from '@/components/ToastNotification';

interface Skill {
  skill_id: string;
  name: string;
  description: string;
  category: string;
  control_id?: string;
  standard?: string;
  severity?: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

interface SkillStats {
  total_skills: number;
  enabled_skills: number;
  disabled_skills: number;
  by_category: Record<string, number>;
  by_standard: Record<string, number>;
}

const Skills: React.FC = () => {
  const { toasts, removeToast, showWarning } = useToast();
  const [skills, setSkills] = useState<Skill[]>([]);
  const [stats, setStats] = useState<SkillStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [filterStandard, setFilterStandard] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [togglingSkill, setTogglingSkill] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  useEffect(() => {
    fetchSkills();
  }, []);

  const fetchSkills = async () => {
    try {
      setLoading(true);
      const response = await apiService.get('/skills');
      setSkills(response.skills || []);
      setStats(response.stats || null);
      setError(null);
    } catch (err) {
      setError('Failed to load skills');
      console.error('Error fetching skills:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleSkill = async (skillId: string, currentState: boolean) => {
    try {
      setTogglingSkill(skillId);
      const endpoint = currentState ? 'disable' : 'enable';
      await apiService.post(`/skills/${skillId}/${endpoint}`);
      
      // Update local state
      setSkills(skills.map(skill => 
        skill.skill_id === skillId 
          ? { ...skill, enabled: !currentState }
          : skill
      ));
      
      // Refresh stats
      await fetchSkills();
    } catch (err) {
      console.error(`Error toggling skill ${skillId}:`, err);
      showWarning('Toggle Failed', 'Failed to toggle skill. Please try again.');
    } finally {
      setTogglingSkill(null);
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case 'detection':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'analysis':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
      case 'remediation':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
    }
  };

  const getSeverityColor = (severity?: string) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'low':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
    }
  };

  const filteredSkills = skills.filter(skill => {
    const matchesCategory = filterCategory === 'all' || skill.category === filterCategory;
    const matchesStandard = filterStandard === 'all' || skill.standard === filterStandard;
    const matchesSearch = searchQuery === '' ||
      skill.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      skill.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      skill.control_id?.toLowerCase().includes(searchQuery.toLowerCase());
    
    return matchesCategory && matchesStandard && matchesSearch;
  });

  // Pagination calculations
  const totalPages = Math.ceil(filteredSkills.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedSkills = filteredSkills.slice(startIndex, endIndex);

  const categories = ['all', ...Array.from(new Set(skills.map(s => s.category)))];
  const standards = ['all', ...Array.from(new Set(skills.map(s => s.standard).filter(Boolean)))];

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, filterCategory, filterStandard]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-800 dark:text-red-200">{error}</p>
        <button
          onClick={fetchSkills}
          className="mt-2 text-sm text-red-600 dark:text-red-400 hover:underline"
        >
          Try again
        </button>
      </div>
    );
  }

  return (
    <>
      <ToastContainer toasts={toasts} onClose={removeToast} />
      <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">
          Agent Skills Management
        </h1>
        <p className="mt-2 text-gray-300">
          Manage detection agent skills and their activation state
        </p>
      </div>

      {/* Stats Cards - Themed Design */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-white/5">
            <div className="text-sm font-medium text-gray-400">
              Total Skills
            </div>
            <div className="mt-2 text-3xl font-bold text-white">
              {stats.total_skills}
            </div>
          </div>
          <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-white/5">
            <div className="text-sm font-medium text-gray-400">
              Enabled
            </div>
            <div className="mt-2 text-3xl font-bold text-green-400">
              {stats.enabled_skills}
            </div>
          </div>
          <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-white/5">
            <div className="text-sm font-medium text-gray-400">
              Disabled
            </div>
            <div className="mt-2 text-3xl font-bold text-gray-400">
              {stats.disabled_skills}
            </div>
          </div>
          <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-white/5">
            <div className="text-sm font-medium text-gray-400">
              Categories
            </div>
            <div className="mt-2 text-3xl font-bold text-orange-400">
              {Object.keys(stats.by_category).length}
            </div>
          </div>
        </div>
      )}

      {/* Filters - Themed Search Bar */}
      <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-sm rounded-xl shadow-lg p-4 border border-white/5">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-semibold text-gray-400 mb-2">
              Search
            </label>
            <div className="relative">
              <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search skills..."
                className="w-full pl-10 pr-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-400 mb-2">
              Category
            </label>
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
            >
              {categories.map(cat => (
                <option key={cat} value={cat} className="bg-gray-800">
                  {cat === 'all' ? 'All Categories' : cat}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-400 mb-2">
              Standard
            </label>
            <select
              value={filterStandard}
              onChange={(e) => setFilterStandard(e.target.value)}
              className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
            >
              {standards.map(std => (
                <option key={std} value={std} className="bg-gray-800">
                  {std === 'all' ? 'All Standards' : std}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Skills List - Modern Design */}
      <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-sm rounded-2xl shadow-2xl overflow-hidden border border-white/5">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b border-white/5">
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Skill
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Standard
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Severity
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-4 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {paginatedSkills.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-400">
                    No skills found matching your filters
                  </td>
                </tr>
              ) : (
                paginatedSkills.map((skill) => (
                  <tr key={skill.skill_id} className="border-b border-white/5 hover:bg-white/5 transition-colors duration-150">
                    <td className="px-6 py-4">
                      <div className="text-sm font-semibold text-white">
                        {skill.name}
                      </div>
                      <div className="text-sm text-gray-400 mt-1 line-clamp-2">
                        {skill.description}
                      </div>
                      {skill.control_id && (
                        <div className="text-xs text-gray-500 mt-1">
                          Control: {skill.control_id}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${
                        skill.category.toLowerCase() === 'detection'
                          ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' :
                        skill.category.toLowerCase() === 'analysis'
                          ? 'bg-orange-500/20 text-orange-400 border-orange-500/30' :
                        skill.category.toLowerCase() === 'remediation'
                          ? 'bg-green-500/20 text-green-400 border-green-500/30' :
                        'bg-gray-500/20 text-gray-400 border-gray-500/30'
                      }`}>
                        {skill.category}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {skill.standard || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {skill.severity ? (
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${
                          skill.severity.toLowerCase() === 'critical'
                            ? 'bg-red-500/20 text-red-400 border-red-500/30' :
                          skill.severity.toLowerCase() === 'high'
                            ? 'bg-orange-500/20 text-orange-400 border-orange-500/30' :
                          skill.severity.toLowerCase() === 'medium'
                            ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' :
                          'bg-blue-500/20 text-blue-400 border-blue-500/30'
                        }`}>
                          {skill.severity.toUpperCase()}
                        </span>
                      ) : (
                        <span className="text-gray-500">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${
                        skill.enabled
                          ? 'bg-green-500/20 text-green-400 border-green-500/30'
                          : 'bg-gray-500/20 text-gray-400 border-gray-500/30'
                      }`}>
                        {skill.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => toggleSkill(skill.skill_id, skill.enabled)}
                        disabled={togglingSkill === skill.skill_id}
                        className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150 ${
                          skill.enabled
                            ? 'bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30'
                            : 'bg-green-500/20 text-green-400 border border-green-500/30 hover:bg-green-500/30'
                        } disabled:opacity-50 disabled:cursor-not-allowed`}
                      >
                        {togglingSkill === skill.skill_id ? (
                          <>
                            <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Processing...
                          </>
                        ) : (
                          skill.enabled ? 'Disable' : 'Enable'
                        )}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {filteredSkills.length > 0 && (
          <div className="px-6 py-4 border-t border-white/5 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-400">
                Showing {startIndex + 1} to {Math.min(endIndex, filteredSkills.length)} of {filteredSkills.length} skills
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

export default Skills;