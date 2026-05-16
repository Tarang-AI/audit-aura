import React, { useState, useEffect } from 'react';
import { Cloud, Plus, RefreshCw, Trash2, Edit, CheckCircle, XCircle, AlertCircle, Activity, X } from 'lucide-react';
import { theme } from '@/config/theme';
import { CloudConnection, ConnectionStats } from '@/types';
import { useToast, ToastContainer } from '@/components/ToastNotification';

type CloudProvider = 'aws' | 'ibm_cloud' | 'azure' | 'gcp' | 'generic';

interface ConnectionFormData {
  name: string;
  provider: CloudProvider;
  description: string;
  region: string;
  enabled: boolean;
  config: Record<string, any>;
}

export const AdminConnections: React.FC = () => {
  const { toasts, removeToast, showSuccess, showWarning } = useToast();
  const [connections, setConnections] = useState<CloudConnection[]>([]);
  const [stats, setStats] = useState<ConnectionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedConnection, setSelectedConnection] = useState<CloudConnection | null>(null);
  const [testingConnection, setTestingConnection] = useState<string | null>(null);
  const [formData, setFormData] = useState<ConnectionFormData>({
    name: '',
    provider: 'ibm_cloud',
    description: '',
    region: '',
    enabled: true,
    config: {}
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadConnections();
    loadStats();
  }, []);

  const loadConnections = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/connections');
      const data = await response.json();
      setConnections(data.connections || []);
    } catch (error) {
      console.error('Failed to load connections:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch('/api/connections/stats/summary');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const testConnection = async (connectionId: string) => {
    try {
      setTestingConnection(connectionId);
      const response = await fetch(`/api/connections/${connectionId}/test`, {
        method: 'POST'
      });
      const result = await response.json();
      
      if (result.success) {
        showSuccess('Connection Test', 'Connection test successful!');
      } else {
        showWarning('Connection Test Failed', result.message || 'Connection test failed');
      }
      
      await loadConnections();
    } catch (error) {
      console.error('Failed to test connection:', error);
      showWarning('Connection Test Failed', 'Failed to test connection');
    } finally {
      setTestingConnection(null);
    }
  };

  const deleteConnection = async (connectionId: string) => {
    if (!confirm('Are you sure you want to delete this connection?')) {
      return;
    }

    try {
      await fetch(`/api/connections/${connectionId}`, {
        method: 'DELETE'
      });
      await loadConnections();
      await loadStats();
    } catch (error) {
      console.error('Failed to delete connection:', error);
      showWarning('Delete Failed', 'Failed to delete connection');
    }
  };

  const toggleConnection = async (connectionId: string, enabled: boolean) => {
    try {
      const endpoint = enabled ? 'enable' : 'disable';
      await fetch(`/api/connections/${connectionId}/${endpoint}`, {
        method: 'POST'
      });
      await loadConnections();
    } catch (error) {
      console.error('Failed to toggle connection:', error);
      showWarning('Toggle Failed', 'Failed to toggle connection');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      provider: 'ibm_cloud',
      description: '',
      region: '',
      enabled: true,
      config: {}
    });
    setFormErrors({});
    setSelectedConnection(null);
    setShowAddModal(false);
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.name.trim()) {
      errors.name = 'Connection name is required';
    }

    // Provider-specific validation
    if (formData.provider === 'aws') {
      if (!formData.config.access_key_id) errors.access_key_id = 'Access Key ID is required';
      if (!formData.config.secret_access_key) errors.secret_access_key = 'Secret Access Key is required';
      if (!formData.config.region) errors.region = 'Region is required';
    } else if (formData.provider === 'ibm_cloud') {
      if (!formData.config.api_key) errors.api_key = 'API Key is required';
      if (!formData.config.region) errors.region = 'Region is required';
    } else if (formData.provider === 'azure') {
      if (!formData.config.tenant_id) errors.tenant_id = 'Tenant ID is required';
      if (!formData.config.client_id) errors.client_id = 'Client ID is required';
      if (!formData.config.client_secret) errors.client_secret = 'Client Secret is required';
      if (!formData.config.subscription_id) errors.subscription_id = 'Subscription ID is required';
    } else if (formData.provider === 'gcp') {
      if (!formData.config.project_id) errors.project_id = 'Project ID is required';
      if (!formData.config.credentials_json) errors.credentials_json = 'Service Account JSON is required';
    } else if (formData.provider === 'generic') {
      if (!formData.config.endpoint_url) errors.endpoint_url = 'Endpoint URL is required';
      if (!formData.config.auth_type) errors.auth_type = 'Auth Type is required';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSaveConnection = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      setSaving(true);
      
      const payload = {
        name: formData.name,
        provider: formData.provider,
        description: formData.description || undefined,
        region: formData.region || undefined,
        enabled: formData.enabled,
        config: formData.config
      };

      if (selectedConnection) {
        // Update existing connection
        await fetch(`/api/connections/${selectedConnection.id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      } else {
        // Create new connection
        const response = await fetch('/api/connections', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Failed to create connection');
        }
      }

      await loadConnections();
      await loadStats();
      resetForm();
      showSuccess(
        selectedConnection ? 'Connection Updated' : 'Connection Created',
        selectedConnection
          ? `${formData.name} has been updated successfully.`
          : `${formData.name} has been created successfully.`
      );
    } catch (error) {
      console.error('Failed to save connection:', error);
      showWarning(
        'Failed to Save Connection',
        error instanceof Error ? error.message : 'An unknown error occurred while saving the connection.'
      );
    } finally {
      setSaving(false);
    }
  };

  const handleEditConnection = (connection: CloudConnection) => {
    setSelectedConnection(connection);
    setFormData({
      name: connection.name,
      provider: connection.provider as CloudProvider,
      description: connection.description || '',
      region: connection.region || '',
      enabled: connection.enabled,
      config: {} // Config will be empty for security, user must re-enter sensitive data
    });
    setShowAddModal(true);
  };

  const updateConfig = (key: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      config: { ...prev.config, [key]: value }
    }));
    // Clear error for this field
    if (formErrors[key]) {
      setFormErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[key];
        return newErrors;
      });
    }
  };

  const renderProviderFields = () => {
    switch (formData.provider) {
      case 'ibm_cloud':
        return (
          <>
            <div>
              <label className={`block text-sm font-medium ${theme.text.primary} mb-2`}>
                IBM Cloud API Key *
              </label>
              <input
                type="password"
                value={formData.config.api_key || ''}
                onChange={(e) => updateConfig('api_key', e.target.value)}
                className={`w-full px-3 py-2 ${theme.bg.secondary} border ${formErrors.api_key ? 'border-red-500' : theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
                placeholder="Your IBM Cloud API Key"
              />
              {formErrors.api_key && (
                <p className="text-red-400 text-sm mt-1">{formErrors.api_key}</p>
              )}
              <p className={`text-xs ${theme.text.secondary} mt-1`}>
                Get your API key from IBM Cloud Console → Manage → Access (IAM) → API keys
              </p>
            </div>
            <div>
              <label className={`block text-sm font-medium ${theme.text.primary} mb-2`}>
                Region *
              </label>
              <select
                value={formData.config.region || 'us-south'}
                onChange={(e) => updateConfig('region', e.target.value)}
                className={`w-full px-3 py-2 ${theme.bg.secondary} border ${formErrors.region ? 'border-red-500' : theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
              >
                <option value="us-south">US South (Dallas)</option>
                <option value="us-east">US East (Washington DC)</option>
                <option value="eu-gb">UK South (London)</option>
                <option value="eu-de">EU Central (Frankfurt)</option>
                <option value="jp-tok">Japan (Tokyo)</option>
                <option value="au-syd">Australia (Sydney)</option>
              </select>
              {formErrors.region && (
                <p className="text-red-400 text-sm mt-1">{formErrors.region}</p>
              )}
            </div>
            
            {/* Event Sources Configuration */}
            <div className="space-y-4 pt-4 border-t border-gray-700">
              <h4 className={`text-md font-semibold ${theme.text.primary}`}>Event Sources</h4>
              
              {/* Activity Tracker */}
              <div className="space-y-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.config.activity_tracker_enabled !== false}
                    onChange={(e) => updateConfig('activity_tracker_enabled', e.target.checked)}
                    className="w-4 h-4 text-cyan-500 bg-gray-700 border-gray-600 rounded focus:ring-cyan-500"
                  />
                  <span className={`text-sm font-medium ${theme.text.primary}`}>IBM Cloud Activity Tracker</span>
                </label>
                {formData.config.activity_tracker_enabled !== false && (
                  <div className="ml-6 space-y-3">
                    <div>
                      <label className={`block text-sm ${theme.text.secondary} mb-1`}>
                        Instance ID
                      </label>
                      <input
                        type="text"
                        value={formData.config.activity_tracker_instance_id || ''}
                        onChange={(e) => updateConfig('activity_tracker_instance_id', e.target.value)}
                        className={`w-full px-3 py-2 ${theme.bg.secondary} border ${theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
                        placeholder="Activity Tracker instance ID"
                      />
                    </div>
                    <div>
                      <label className={`block text-sm ${theme.text.secondary} mb-1`}>
                        CRN (Optional)
                      </label>
                      <input
                        type="text"
                        value={formData.config.activity_tracker_crn || ''}
                        onChange={(e) => updateConfig('activity_tracker_crn', e.target.value)}
                        className={`w-full px-3 py-2 ${theme.bg.secondary} border ${theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
                        placeholder="crn:v1:bluemix:public:logdnaat:..."
                      />
                    </div>
                  </div>
                )}
              </div>
              
              {/* Platform Logs */}
              <div className="space-y-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.config.platform_logs_enabled === true}
                    onChange={(e) => updateConfig('platform_logs_enabled', e.target.checked)}
                    className="w-4 h-4 text-cyan-500 bg-gray-700 border-gray-600 rounded focus:ring-cyan-500"
                  />
                  <span className={`text-sm font-medium ${theme.text.primary}`}>IBM Cloud Platform Logs</span>
                </label>
                {formData.config.platform_logs_enabled === true && (
                  <div className="ml-6 space-y-3">
                    <div>
                      <label className={`block text-sm ${theme.text.secondary} mb-1`}>
                        Logs Instance ID
                      </label>
                      <input
                        type="text"
                        value={formData.config.logs_instance_id || ''}
                        onChange={(e) => updateConfig('logs_instance_id', e.target.value)}
                        className={`w-full px-3 py-2 ${theme.bg.secondary} border ${theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
                        placeholder="Platform Logs instance ID"
                      />
                    </div>
                    <div>
                      <label className={`block text-sm ${theme.text.secondary} mb-1`}>
                        Ingestion Key (Optional)
                      </label>
                      <input
                        type="password"
                        value={formData.config.logs_ingestion_key || ''}
                        onChange={(e) => updateConfig('logs_ingestion_key', e.target.value)}
                        className={`w-full px-3 py-2 ${theme.bg.secondary} border ${theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
                        placeholder="Ingestion key for Platform Logs"
                      />
                    </div>
                  </div>
                )}
              </div>
              
              {/* Monitoring */}
              <div className="space-y-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.config.monitoring_enabled === true}
                    onChange={(e) => updateConfig('monitoring_enabled', e.target.checked)}
                    className="w-4 h-4 text-cyan-500 bg-gray-700 border-gray-600 rounded focus:ring-cyan-500"
                  />
                  <span className={`text-sm font-medium ${theme.text.primary}`}>IBM Cloud Monitoring</span>
                </label>
                {formData.config.monitoring_enabled === true && (
                  <div className="ml-6">
                    <label className={`block text-sm ${theme.text.secondary} mb-1`}>
                      Monitoring Instance ID
                    </label>
                    <input
                      type="text"
                      value={formData.config.monitoring_instance_id || ''}
                      onChange={(e) => updateConfig('monitoring_instance_id', e.target.value)}
                      className={`w-full px-3 py-2 ${theme.bg.secondary} border ${theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
                      placeholder="Monitoring instance ID"
                    />
                  </div>
                )}
              </div>
            </div>
          </>
        );

      case 'aws':
        return (
          <>
            <div>
              <label className={`block text-sm font-medium ${theme.text.primary} mb-2`}>
                Access Key ID *
              </label>
              <input
                type="text"
                value={formData.config.access_key_id || ''}
                onChange={(e) => updateConfig('access_key_id', e.target.value)}
                className={`w-full px-3 py-2 ${theme.bg.secondary} border ${formErrors.access_key_id ? 'border-red-500' : theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
                placeholder="AKIAIOSFODNN7EXAMPLE"
              />
              {formErrors.access_key_id && (
                <p className="text-red-400 text-sm mt-1">{formErrors.access_key_id}</p>
              )}
            </div>
            <div>
              <label className={`block text-sm font-medium ${theme.text.primary} mb-2`}>
                Secret Access Key *
              </label>
              <input
                type="password"
                value={formData.config.secret_access_key || ''}
                onChange={(e) => updateConfig('secret_access_key', e.target.value)}
                className={`w-full px-3 py-2 ${theme.bg.secondary} border ${formErrors.secret_access_key ? 'border-red-500' : theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
                placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
              />
              {formErrors.secret_access_key && (
                <p className="text-red-400 text-sm mt-1">{formErrors.secret_access_key}</p>
              )}
            </div>
            <div>
              <label className={`block text-sm font-medium ${theme.text.primary} mb-2`}>
                Region *
              </label>
              <input
                type="text"
                value={formData.config.region || ''}
                onChange={(e) => updateConfig('region', e.target.value)}
                className={`w-full px-3 py-2 ${theme.bg.secondary} border ${formErrors.region ? 'border-red-500' : theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
                placeholder="us-east-1"
              />
              {formErrors.region && (
                <p className="text-red-400 text-sm mt-1">{formErrors.region}</p>
              )}
            </div>
            
            {/* Event Sources Configuration for AWS */}
            <div className="space-y-4 pt-4 border-t border-gray-700">
              <h4 className={`text-md font-semibold ${theme.text.primary}`}>Event Sources</h4>
              
              {/* CloudTrail */}
              <div className="space-y-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.config.cloudtrail_enabled !== false}
                    onChange={(e) => updateConfig('cloudtrail_enabled', e.target.checked)}
                    className="w-4 h-4 text-cyan-500 bg-gray-700 border-gray-600 rounded focus:ring-cyan-500"
                  />
                  <span className={`text-sm font-medium ${theme.text.primary}`}>AWS CloudTrail Events</span>
                </label>
                {formData.config.cloudtrail_enabled !== false && (
                  <div className="ml-6 space-y-3">
                    <div>
                      <label className={`block text-sm ${theme.text.secondary} mb-1`}>
                        CloudWatch Log Group (Optional)
                      </label>
                      <input
                        type="text"
                        value={formData.config.cloudtrail_log_group || ''}
                        onChange={(e) => updateConfig('cloudtrail_log_group', e.target.value)}
                        className={`w-full px-3 py-2 ${theme.bg.secondary} border ${theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
                        placeholder="/aws/cloudtrail/logs"
                      />
                      <p className={`text-xs ${theme.text.secondary} mt-1`}>
                        CloudWatch Log Group where CloudTrail logs are sent
                      </p>
                    </div>
                    <div>
                      <label className={`block text-sm ${theme.text.secondary} mb-1`}>
                        S3 Bucket (Optional)
                      </label>
                      <input
                        type="text"
                        value={formData.config.cloudtrail_s3_bucket || ''}
                        onChange={(e) => updateConfig('cloudtrail_s3_bucket', e.target.value)}
                        className={`w-full px-3 py-2 ${theme.bg.secondary} border ${theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
                        placeholder="my-cloudtrail-bucket"
                      />
                      <p className={`text-xs ${theme.text.secondary} mt-1`}>
                        S3 bucket where CloudTrail logs are stored
                      </p>
                    </div>
                  </div>
                )}
              </div>
              
              {/* CloudWatch Logs */}
              <div className="space-y-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.config.cloudwatch_enabled === true}
                    onChange={(e) => updateConfig('cloudwatch_enabled', e.target.checked)}
                    className="w-4 h-4 text-cyan-500 bg-gray-700 border-gray-600 rounded focus:ring-cyan-500"
                  />
                  <span className={`text-sm font-medium ${theme.text.primary}`}>AWS CloudWatch Logs</span>
                </label>
              </div>
              
              {/* AWS Config */}
              <div className="space-y-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.config.config_enabled === true}
                    onChange={(e) => updateConfig('config_enabled', e.target.checked)}
                    className="w-4 h-4 text-cyan-500 bg-gray-700 border-gray-600 rounded focus:ring-cyan-500"
                  />
                  <span className={`text-sm font-medium ${theme.text.primary}`}>AWS Config</span>
                </label>
              </div>
            </div>
          </>
        );

      case 'azure':
        return (
          <>
            <div>
              <label className={`block text-sm font-medium ${theme.text.primary} mb-2`}>
                Tenant ID *
              </label>
              <input
                type="text"
                value={formData.config.tenant_id || ''}
                onChange={(e) => updateConfig('tenant_id', e.target.value)}
                className={`w-full px-3 py-2 ${theme.bg.secondary} border ${formErrors.tenant_id ? 'border-red-500' : theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
                placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              />
              {formErrors.tenant_id && (
                <p className="text-red-400 text-sm mt-1">{formErrors.tenant_id}</p>
              )}
            </div>
            <div>
              <label className={`block text-sm font-medium ${theme.text.primary} mb-2`}>
                Client ID *
              </label>
              <input
                type="text"
                value={formData.config.client_id || ''}
                onChange={(e) => updateConfig('client_id', e.target.value)}
                className={`w-full px-3 py-2 ${theme.bg.secondary} border ${formErrors.client_id ? 'border-red-500' : theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
                placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              />
              {formErrors.client_id && (
                <p className="text-red-400 text-sm mt-1">{formErrors.client_id}</p>
              )}
            </div>
            <div>
              <label className={`block text-sm font-medium ${theme.text.primary} mb-2`}>
                Client Secret *
              </label>
              <input
                type="password"
                value={formData.config.client_secret || ''}
                onChange={(e) => updateConfig('client_secret', e.target.value)}
                className={`w-full px-3 py-2 ${theme.bg.secondary} border ${formErrors.client_secret ? 'border-red-500' : theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
                placeholder="Your client secret"
              />
              {formErrors.client_secret && (
                <p className="text-red-400 text-sm mt-1">{formErrors.client_secret}</p>
              )}
            </div>
            <div>
              <label className={`block text-sm font-medium ${theme.text.primary} mb-2`}>
                Subscription ID *
              </label>
              <input
                type="text"
                value={formData.config.subscription_id || ''}
                onChange={(e) => updateConfig('subscription_id', e.target.value)}
                className={`w-full px-3 py-2 ${theme.bg.secondary} border ${formErrors.subscription_id ? 'border-red-500' : theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
                placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              />
              {formErrors.subscription_id && (
                <p className="text-red-400 text-sm mt-1">{formErrors.subscription_id}</p>
              )}
            </div>
          </>
        );

      case 'gcp':
        return (
          <>
            <div>
              <label className={`block text-sm font-medium ${theme.text.primary} mb-2`}>
                Project ID *
              </label>
              <input
                type="text"
                value={formData.config.project_id || ''}
                onChange={(e) => updateConfig('project_id', e.target.value)}
                className={`w-full px-3 py-2 ${theme.bg.secondary} border ${formErrors.project_id ? 'border-red-500' : theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
                placeholder="my-project-id"
              />
              {formErrors.project_id && (
                <p className="text-red-400 text-sm mt-1">{formErrors.project_id}</p>
              )}
            </div>
            <div>
              <label className={`block text-sm font-medium ${theme.text.primary} mb-2`}>
                Service Account JSON *
              </label>
              <textarea
                value={formData.config.credentials_json || ''}
                onChange={(e) => updateConfig('credentials_json', e.target.value)}
                rows={6}
                className={`w-full px-3 py-2 ${theme.bg.secondary} border ${formErrors.credentials_json ? 'border-red-500' : theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500 font-mono text-sm`}
                placeholder='{"type": "service_account", "project_id": "...", ...}'
              />
              {formErrors.credentials_json && (
                <p className="text-red-400 text-sm mt-1">{formErrors.credentials_json}</p>
              )}
            </div>
          </>
        );

      case 'generic':
        return (
          <>
            <div>
              <label className={`block text-sm font-medium ${theme.text.primary} mb-2`}>
                Endpoint URL *
              </label>
              <input
                type="url"
                value={formData.config.endpoint_url || ''}
                onChange={(e) => updateConfig('endpoint_url', e.target.value)}
                className={`w-full px-3 py-2 ${theme.bg.secondary} border ${formErrors.endpoint_url ? 'border-red-500' : theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
                placeholder="https://api.example.com"
              />
              {formErrors.endpoint_url && (
                <p className="text-red-400 text-sm mt-1">{formErrors.endpoint_url}</p>
              )}
            </div>
            <div>
              <label className={`block text-sm font-medium ${theme.text.primary} mb-2`}>
                Authentication Type *
              </label>
              <select
                value={formData.config.auth_type || 'api_key'}
                onChange={(e) => updateConfig('auth_type', e.target.value)}
                className={`w-full px-3 py-2 ${theme.bg.secondary} border ${theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
              >
                <option value="api_key">API Key</option>
                <option value="bearer">Bearer Token</option>
                <option value="basic">Basic Auth</option>
              </select>
            </div>
            {formData.config.auth_type === 'api_key' && (
              <div>
                <label className={`block text-sm font-medium ${theme.text.primary} mb-2`}>
                  API Key
                </label>
                <input
                  type="password"
                  value={formData.config.api_key || ''}
                  onChange={(e) => updateConfig('api_key', e.target.value)}
                  className={`w-full px-3 py-2 ${theme.bg.secondary} border ${theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
                  placeholder="Your API key"
                />
              </div>
            )}
            {formData.config.auth_type === 'bearer' && (
              <div>
                <label className={`block text-sm font-medium ${theme.text.primary} mb-2`}>
                  Bearer Token
                </label>
                <input
                  type="password"
                  value={formData.config.bearer_token || ''}
                  onChange={(e) => updateConfig('bearer_token', e.target.value)}
                  className={`w-full px-3 py-2 ${theme.bg.secondary} border ${theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
                  placeholder="Your bearer token"
                />
              </div>
            )}
          </>
        );

      default:
        return null;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-5 w-5 text-green-400" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-400" />;
      case 'testing':
        return <RefreshCw className="h-5 w-5 text-yellow-400 animate-spin" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-400" />;
    }
  };

  const getProviderLabel = (provider: string) => {
    const labels: Record<string, string> = {
      aws: 'AWS',
      ibm_cloud: 'IBM Cloud',
      azure: 'Azure',
      gcp: 'Google Cloud',
      generic: 'Generic'
    };
    return labels[provider] || provider;
  };

  const getProviderColor = (provider: string) => {
    const colors: Record<string, string> = {
      aws: 'bg-orange-500/20 text-orange-400',
      ibm_cloud: 'bg-blue-500/20 text-blue-400',
      azure: 'bg-cyan-500/20 text-cyan-400',
      gcp: 'bg-green-500/20 text-green-400',
      generic: 'bg-orange-500/20 text-orange-400'
    };
    return colors[provider] || 'bg-gray-500/20 text-gray-400';
  };

  return (
    <>
      <ToastContainer toasts={toasts} onClose={removeToast} />
      <div className="space-y-6">
        <div className="flex items-center justify-between">
        <div>
          <h1 className={`text-3xl font-bold ${theme.text.primary}`}>Cloud Connections</h1>
          <p className={`${theme.text.secondary} mt-1`}>Manage cloud provider connections and credentials</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className={`flex items-center gap-2 px-4 py-2 ${theme.button.primary} rounded-lg transition-colors`}
        >
          <Plus className="h-5 w-5" />
          Add Connection
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className={`${theme.bg.card} rounded-xl p-6 border ${theme.border.primary}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm ${theme.text.secondary}`}>Total Connections</p>
                <p className={`text-2xl font-bold ${theme.text.primary} mt-1`}>{stats.total_connections}</p>
              </div>
              <Cloud className="h-8 w-8 text-cyan-400" />
            </div>
          </div>

          <div className={`${theme.bg.card} rounded-xl p-6 border ${theme.border.primary}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm ${theme.text.secondary}`}>Active</p>
                <p className={`text-2xl font-bold text-green-400 mt-1`}>{stats.active_connections}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-400" />
            </div>
          </div>

          <div className={`${theme.bg.card} rounded-xl p-6 border ${theme.border.primary}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm ${theme.text.secondary}`}>Errors</p>
                <p className={`text-2xl font-bold text-red-400 mt-1`}>{stats.error_connections}</p>
              </div>
              <XCircle className="h-8 w-8 text-red-400" />
            </div>
          </div>

          <div className={`${theme.bg.card} rounded-xl p-6 border ${theme.border.primary}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm ${theme.text.secondary}`}>Events Processed</p>
                <p className={`text-2xl font-bold ${theme.text.primary} mt-1`}>
                  {(stats.total_events_processed || 0).toLocaleString()}
                </p>
              </div>
              <Activity className="h-8 w-8 text-cyan-400" />
            </div>
          </div>
        </div>
      )}

      {/* Connections List */}
      <div className={`${theme.bg.card} rounded-xl shadow-sm border ${theme.border.primary}`}>
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className={`text-xl font-semibold ${theme.text.primary}`}>Connections</h2>
            <button
              onClick={loadConnections}
              className={`p-2 ${theme.button.secondary} rounded-lg transition-colors`}
            >
              <RefreshCw className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="p-6">
          {loading ? (
            <div className="text-center py-8">
              <RefreshCw className="h-8 w-8 text-cyan-400 animate-spin mx-auto" />
              <p className={`${theme.text.secondary} mt-2`}>Loading connections...</p>
            </div>
          ) : connections.length === 0 ? (
            <div className="text-center py-12">
              <Cloud className="h-16 w-16 text-gray-600 mx-auto mb-4" />
              <p className={`${theme.text.secondary} text-lg`}>No connections configured</p>
              <p className={`${theme.text.secondary} text-sm mt-2`}>
                Add your first cloud provider connection to start monitoring
              </p>
              <button
                onClick={() => setShowAddModal(true)}
                className={`mt-4 px-6 py-2 ${theme.button.primary} rounded-lg transition-colors`}
              >
                Add Connection
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {connections.map((connection) => (
                <div
                  key={connection.id}
                  className={`p-4 rounded-lg border ${theme.border.primary} ${theme.bg.secondary} hover:border-cyan-500/50 transition-colors`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        {getStatusIcon(connection.status)}
                        <h3 className={`text-lg font-semibold ${theme.text.primary}`}>
                          {connection.name}
                        </h3>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getProviderColor(connection.provider)}`}>
                          {getProviderLabel(connection.provider)}
                        </span>
                        {connection.region && (
                          <span className={`px-2 py-1 rounded text-xs ${theme.text.secondary} bg-gray-700`}>
                            {connection.region}
                          </span>
                        )}
                      </div>

                      {connection.description && (
                        <p className={`${theme.text.secondary} text-sm mb-3`}>{connection.description}</p>
                      )}

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <p className={`${theme.text.secondary}`}>Status</p>
                          <p className={`${theme.text.primary} font-medium capitalize`}>{connection.status}</p>
                        </div>
                        <div>
                          <p className={`${theme.text.secondary}`}>Events Processed</p>
                          <p className={`${theme.text.primary} font-medium`}>
                            {(connection.events_processed || 0).toLocaleString()}
                          </p>
                        </div>
                        <div>
                          <p className={`${theme.text.secondary}`}>Last Tested</p>
                          <p className={`${theme.text.primary} font-medium`}>
                            {connection.last_tested_at
                              ? new Date(connection.last_tested_at).toLocaleDateString()
                              : 'Never'}
                          </p>
                        </div>
                        <div>
                          <p className={`${theme.text.secondary}`}>Errors</p>
                          <p className={`${theme.text.primary} font-medium`}>{connection.error_count}</p>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 ml-4">
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={connection.enabled}
                          onChange={(e) => toggleConnection(connection.id, e.target.checked)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-cyan-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-500"></div>
                      </label>

                      <button
                        onClick={() => testConnection(connection.id)}
                        disabled={testingConnection === connection.id}
                        className={`p-2 ${theme.button.secondary} rounded-lg transition-colors disabled:opacity-50`}
                        title="Test Connection"
                      >
                        <RefreshCw
                          className={`h-4 w-4 ${testingConnection === connection.id ? 'animate-spin' : ''}`}
                        />
                      </button>

                      <button
                        onClick={() => handleEditConnection(connection)}
                        className={`p-2 ${theme.button.secondary} rounded-lg transition-colors`}
                        title="Edit Connection"
                      >
                        <Edit className="h-4 w-4" />
                      </button>

                      <button
                        onClick={() => deleteConnection(connection.id)}
                        className="p-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors"
                        title="Delete Connection"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Add/Edit Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className={`${theme.bg.card} rounded-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto border ${theme.border.primary}`}>
            <div className="p-6 border-b border-gray-700 flex items-center justify-between">
              <h2 className={`text-2xl font-bold ${theme.text.primary}`}>
                {selectedConnection ? 'Edit Connection' : 'Add Cloud Connection'}
              </h2>
              <button
                onClick={resetForm}
                className={`p-2 ${theme.button.secondary} rounded-lg transition-colors`}
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-6">
              {/* Basic Information */}
              <div className="space-y-4">
                <h3 className={`text-lg font-semibold ${theme.text.primary}`}>Basic Information</h3>
                
                <div>
                  <label className={`block text-sm font-medium ${theme.text.primary} mb-2`}>
                    Connection Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className={`w-full px-3 py-2 ${theme.bg.secondary} border ${formErrors.name ? 'border-red-500' : theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
                    placeholder="My IBM Cloud Account"
                  />
                  {formErrors.name && (
                    <p className="text-red-400 text-sm mt-1">{formErrors.name}</p>
                  )}
                </div>

                <div>
                  <label className={`block text-sm font-medium ${theme.text.primary} mb-2`}>
                    Cloud Provider *
                  </label>
                  <select
                    value={formData.provider}
                    onChange={(e) => setFormData(prev => ({ ...prev, provider: e.target.value as CloudProvider, config: {} }))}
                    disabled={!!selectedConnection}
                    className={`w-full px-3 py-2 ${theme.bg.secondary} border ${theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500 disabled:opacity-50`}
                  >
                    <option value="ibm_cloud">IBM Cloud</option>
                    <option value="aws">AWS</option>
                    <option value="azure">Azure</option>
                    <option value="gcp">Google Cloud</option>
                    <option value="generic">Generic</option>
                  </select>
                  {selectedConnection && (
                    <p className={`text-xs ${theme.text.secondary} mt-1`}>
                      Provider cannot be changed for existing connections
                    </p>
                  )}
                </div>

                <div>
                  <label className={`block text-sm font-medium ${theme.text.primary} mb-2`}>
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    rows={2}
                    className={`w-full px-3 py-2 ${theme.bg.secondary} border ${theme.border.primary} rounded-lg ${theme.text.primary} focus:outline-none focus:ring-2 focus:ring-cyan-500`}
                    placeholder="Optional description for this connection"
                  />
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="enabled"
                    checked={formData.enabled}
                    onChange={(e) => setFormData(prev => ({ ...prev, enabled: e.target.checked }))}
                    className="w-4 h-4 text-cyan-500 bg-gray-700 border-gray-600 rounded focus:ring-cyan-500"
                  />
                  <label htmlFor="enabled" className={`text-sm ${theme.text.primary} cursor-pointer`}>
                    Enable connection immediately
                  </label>
                </div>
              </div>

              {/* Provider-Specific Configuration */}
              <div className="space-y-4">
                <h3 className={`text-lg font-semibold ${theme.text.primary}`}>
                  {getProviderLabel(formData.provider)} Configuration
                </h3>
                {renderProviderFields()}
              </div>

              {selectedConnection && (
                <div className={`p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/30`}>
                  <p className={`text-sm text-yellow-400`}>
                    <strong>Note:</strong> For security reasons, you must re-enter sensitive credentials when editing a connection.
                  </p>
                </div>
              )}
            </div>

            <div className="p-6 border-t border-gray-700 flex justify-end gap-3">
              <button
                onClick={resetForm}
                disabled={saving}
                className={`px-6 py-2 ${theme.button.secondary} rounded-lg transition-colors disabled:opacity-50`}
              >
                Cancel
              </button>
              <button
                onClick={handleSaveConnection}
                disabled={saving}
                className={`px-6 py-2 ${theme.button.primary} rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2`}
              >
                {saving ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    {selectedConnection ? 'Update Connection' : 'Create Connection'}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
      </div>
    </>
  );
};

// Made with Bob