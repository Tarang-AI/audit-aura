import React from 'react';
import { Bell, Mail, Shield, Database } from 'lucide-react';

export const AdminSettings: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Settings</h1>
        <p className="text-gray-300 mt-1">Configure system settings and preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Notification Settings */}
        <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-white/5">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-orange-500/20 border border-orange-500/30">
              <Bell className="h-6 w-6 text-orange-400" />
            </div>
            <h2 className="text-xl font-semibold text-white">Notifications</h2>
          </div>
          <div className="space-y-4">
            <label className="flex items-center justify-between cursor-pointer group">
              <span className="text-gray-300 group-hover:text-white transition-colors">Email Notifications</span>
              <input type="checkbox" defaultChecked className="w-5 h-5 text-orange-500 bg-gray-800 border-gray-600 rounded focus:ring-orange-500 focus:ring-2" />
            </label>
            <label className="flex items-center justify-between cursor-pointer group">
              <span className="text-gray-300 group-hover:text-white transition-colors">Slack Notifications</span>
              <input type="checkbox" defaultChecked className="w-5 h-5 text-orange-500 bg-gray-800 border-gray-600 rounded focus:ring-orange-500 focus:ring-2" />
            </label>
            <label className="flex items-center justify-between cursor-pointer group">
              <span className="text-gray-300 group-hover:text-white transition-colors">WebSocket Alerts</span>
              <input type="checkbox" defaultChecked className="w-5 h-5 text-orange-500 bg-gray-800 border-gray-600 rounded focus:ring-orange-500 focus:ring-2" />
            </label>
          </div>
        </div>

        {/* Email Configuration */}
        <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-white/5">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-orange-500/20 border border-orange-500/30">
              <Mail className="h-6 w-6 text-orange-400" />
            </div>
            <h2 className="text-xl font-semibold text-white">Email Configuration</h2>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-400 mb-2">SMTP Host</label>
              <input
                type="text"
                placeholder="smtp.example.com"
                className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-400 mb-2">SMTP Port</label>
              <input
                type="number"
                placeholder="587"
                className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
              />
            </div>
          </div>
        </div>

        {/* Security Settings */}
        <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-white/5">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-orange-500/20 border border-orange-500/30">
              <Shield className="h-6 w-6 text-orange-400" />
            </div>
            <h2 className="text-xl font-semibold text-white">Security</h2>
          </div>
          <div className="space-y-4">
            <label className="flex items-center justify-between cursor-pointer group">
              <span className="text-gray-300 group-hover:text-white transition-colors">Two-Factor Authentication</span>
              <input type="checkbox" className="w-5 h-5 text-orange-500 bg-gray-800 border-gray-600 rounded focus:ring-orange-500 focus:ring-2" />
            </label>
            <label className="flex items-center justify-between cursor-pointer group">
              <span className="text-gray-300 group-hover:text-white transition-colors">Auto-Remediation</span>
              <input type="checkbox" defaultChecked className="w-5 h-5 text-orange-500 bg-gray-800 border-gray-600 rounded focus:ring-orange-500 focus:ring-2" />
            </label>
          </div>
        </div>

        {/* Data Retention */}
        <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-white/5">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-orange-500/20 border border-orange-500/30">
              <Database className="h-6 w-6 text-orange-400" />
            </div>
            <h2 className="text-xl font-semibold text-white">Data Retention</h2>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-400 mb-2">Violation History (days)</label>
              <input
                type="number"
                defaultValue="90"
                className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-400 mb-2">Log Retention (days)</label>
              <input
                type="number"
                defaultValue="30"
                className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end gap-3">
        <button className="px-6 py-2.5 bg-gray-800/50 border border-gray-700/50 text-gray-300 rounded-lg hover:bg-gray-700/50 hover:text-white transition-all font-medium">
          Cancel
        </button>
        <button className="px-6 py-2.5 bg-gradient-to-r from-orange-500 to-amber-500 text-white rounded-lg hover:from-orange-600 hover:to-amber-600 transition-all font-medium shadow-lg shadow-orange-500/20">
          Save Changes
        </button>
      </div>
    </div>
  );
};

// Made with Bob
