import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface Violation {
  id: string;
  severity: string;
  standard: string;
  control_id: string;
  description: string;
  timestamp: string;
  status: string;
}

interface ComplianceState {
  // Data
  alerts: any[];
  dashboardData: any | null;
  complianceScore: number;
  violations: Violation[];
  loading: boolean;
  error: string | null;

  // Actions
  addAlert: (alert: any) => void;
  clearAlerts: () => void;
  setDashboardData: (data: any) => void;
  setComplianceScore: (score: number) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  decrementScore: (amount: number) => void;
  fetchDashboard: () => Promise<void>;
}

export const useComplianceStore = create<ComplianceState>()(
  devtools(
    (set, get) => ({
      // Initial state - empty until data is fetched
      alerts: [],
      dashboardData: null,
      complianceScore: 0,
      violations: [],
      loading: false,
      error: null,

      // Actions
      addAlert: (alert) =>
        set((state) => ({
          alerts: [alert, ...state.alerts].slice(0, 50),
        })),

      clearAlerts: () => set({ alerts: [] }),

      setDashboardData: (data) =>
        set({
          dashboardData: data,
          complianceScore: data.compliance_score?.overall_score ?? 85,
        }),

      setComplianceScore: (score) => set({ complianceScore: score }),

      setLoading: (loading) => set({ loading }),

      setError: (error) => set({ error }),

      decrementScore: (amount) =>
        set((state) => ({
          complianceScore: Math.max(0, state.complianceScore - amount),
        })),

      fetchDashboard: async () => {
        set({ loading: true, error: null });
        
        // Check if mock mode is enabled via environment variable
        const mockMode = import.meta.env.VITE_MOCK_MODE === 'true';
        
        if (mockMode) {
          // Use mock data when MOCK_MODE is enabled
          set({
            dashboardData: {
              compliance_score: {
                overall_score: 0.78,
                standards: {
                  'SOC2': { score: 0.75, violations: 4, controls: 64 },
                  'HIPAA': { score: 0.72, violations: 2, controls: 45 },
                  'PCI-DSS': { score: 0.85, violations: 1, controls: 78 },
                  'ISO27001': { score: 0.88, violations: 0, controls: 114 },
                  'GDPR': { score: 0.80, violations: 1, controls: 32 }
                }
              }
            },
            complianceScore: 78,
            violations: [
              {
                id: '1',
                severity: 'high',
                standard: 'SOC2',
                control_id: 'CC6.1',
                description: 'S3 bucket public access detected',
                timestamp: new Date().toISOString(),
                status: 'open',
              },
              {
                id: '2',
                severity: 'medium',
                standard: 'HIPAA',
                control_id: 'HP-164.312',
                description: 'Encryption not enabled',
                timestamp: new Date().toISOString(),
                status: 'open',
              },
            ],
            loading: false,
          });
          return;
        }
        
        // Fetch real data from API
        try {
          const { withAppId } = await import('@/utils/appParam');
          const response = await fetch(withAppId('/dashboard'));
          if (response.ok) {
            const data = await response.json();
            
            // Extract compliance score correctly - handle both object and number formats
            let score = 85;
            if (data.compliance_score) {
              if (typeof data.compliance_score === 'object') {
                score = data.compliance_score.overall_score || data.compliance_score.overall || 85;
              } else {
                score = data.compliance_score;
              }
            }
            
            set({
              dashboardData: data,
              complianceScore: score,
              violations: data.violations || [],
              loading: false,
            });
          } else {
            set({
              dashboardData: null,
              complianceScore: 0,
              violations: [],
              loading: false,
              error: 'Failed to fetch dashboard data',
            });
          }
        } catch (error) {
          console.error('Failed to fetch dashboard:', error);
          set({
            dashboardData: null,
            complianceScore: 0,
            violations: [],
            loading: false,
            error: 'Failed to connect to backend',
          });
        }
      },
    }),
    { name: 'ComplianceStore' }
  )
);

// Made with Bob
