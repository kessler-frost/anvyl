import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Save,
  RefreshCw,
  Shield,
  Globe,
  Database,
  Bell,
  Palette,
  Monitor,
  Key,
  Users,
  Activity,
  AlertTriangle
} from 'lucide-react'

const SettingsView = () => {
  const [activeTab, setActiveTab] = useState('general')
  const [settings, setSettings] = useState({
    serverHost: 'localhost',
    serverPort: '50051',
    autoRefresh: true,
    refreshInterval: '30',
    theme: 'dark',
    notifications: true,
    logLevel: 'info',
    maxLogSize: '100',
    enableAuth: false,
    sessionTimeout: '30',
    enableTLS: false,
    retryAttempts: '3',
    connectionTimeout: '10'
  })

  const tabs = [
    { id: 'general', name: 'General', icon: Monitor },
    { id: 'connection', name: 'Connection', icon: Globe },
    { id: 'security', name: 'Security', icon: Shield },
    { id: 'notifications', name: 'Notifications', icon: Bell },
    { id: 'logging', name: 'Logging', icon: Database },
    { id: 'advanced', name: 'Advanced', icon: Activity }
  ]

  const handleSettingChange = (key: string, value: string | boolean) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  const renderGeneralSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">General Settings</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-white/80 mb-2">Theme</label>
            <select 
              value={settings.theme}
              onChange={(e) => handleSettingChange('theme', e.target.value)}
              className="input-glass w-full"
            >
              <option value="dark">Dark</option>
              <option value="light">Light</option>
              <option value="auto">Auto</option>
            </select>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm text-white/80">Auto Refresh</label>
              <p className="text-xs text-white/60">Automatically refresh data</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input 
                type="checkbox" 
                checked={settings.autoRefresh}
                onChange={(e) => handleSettingChange('autoRefresh', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-white/20 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          {settings.autoRefresh && (
            <div>
              <label className="block text-sm text-white/80 mb-2">Refresh Interval (seconds)</label>
              <input 
                type="number"
                value={settings.refreshInterval}
                onChange={(e) => handleSettingChange('refreshInterval', e.target.value)}
                className="input-glass w-full"
                min="5"
                max="300"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )

  const renderConnectionSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">Connection Settings</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-white/80 mb-2">Server Host</label>
            <input 
              type="text"
              value={settings.serverHost}
              onChange={(e) => handleSettingChange('serverHost', e.target.value)}
              className="input-glass w-full"
              placeholder="localhost"
            />
          </div>
          
          <div>
            <label className="block text-sm text-white/80 mb-2">Server Port</label>
            <input 
              type="number"
              value={settings.serverPort}
              onChange={(e) => handleSettingChange('serverPort', e.target.value)}
              className="input-glass w-full"
              min="1"
              max="65535"
            />
          </div>

          <div>
            <label className="block text-sm text-white/80 mb-2">Connection Timeout (seconds)</label>
            <input 
              type="number"
              value={settings.connectionTimeout}
              onChange={(e) => handleSettingChange('connectionTimeout', e.target.value)}
              className="input-glass w-full"
              min="5"
              max="60"
            />
          </div>

          <div>
            <label className="block text-sm text-white/80 mb-2">Retry Attempts</label>
            <input 
              type="number"
              value={settings.retryAttempts}
              onChange={(e) => handleSettingChange('retryAttempts', e.target.value)}
              className="input-glass w-full"
              min="1"
              max="10"
            />
          </div>

          <div className="glass p-4 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <Activity className="w-4 h-4 text-green-400" />
              <span className="text-sm text-white/80">Connection Status</span>
            </div>
            <div className="text-sm text-green-300">Connected to localhost:50051</div>
            <div className="text-xs text-white/60 mt-1">Last connected: 2 minutes ago</div>
          </div>
        </div>
      </div>
    </div>
  )

  const renderSecuritySettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">Security Settings</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm text-white/80">Enable Authentication</label>
              <p className="text-xs text-white/60">Require authentication for API access</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input 
                type="checkbox" 
                checked={settings.enableAuth}
                onChange={(e) => handleSettingChange('enableAuth', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-white/20 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm text-white/80">Enable TLS</label>
              <p className="text-xs text-white/60">Use encrypted connections</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input 
                type="checkbox" 
                checked={settings.enableTLS}
                onChange={(e) => handleSettingChange('enableTLS', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-white/20 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          {settings.enableAuth && (
            <div>
              <label className="block text-sm text-white/80 mb-2">Session Timeout (minutes)</label>
              <input 
                type="number"
                value={settings.sessionTimeout}
                onChange={(e) => handleSettingChange('sessionTimeout', e.target.value)}
                className="input-glass w-full"
                min="5"
                max="1440"
              />
            </div>
          )}

          <div className="glass p-4 rounded-lg border-l-4 border-yellow-500">
            <div className="flex items-center space-x-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-yellow-400" />
              <span className="text-sm text-white/80">Security Notice</span>
            </div>
            <div className="text-sm text-white/70">
              For production environments, it's recommended to enable both authentication and TLS.
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  const renderNotificationSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">Notification Settings</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm text-white/80">Enable Notifications</label>
              <p className="text-xs text-white/60">Show system notifications</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input 
                type="checkbox" 
                checked={settings.notifications}
                onChange={(e) => handleSettingChange('notifications', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-white/20 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          {settings.notifications && (
            <div className="space-y-4 ml-6 pl-4 border-l border-white/20">
              <div className="flex items-center justify-between">
                <span className="text-sm text-white/80">Host status changes</span>
                <input type="checkbox" defaultChecked className="rounded" />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-white/80">Container events</span>
                <input type="checkbox" defaultChecked className="rounded" />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-white/80">Agent failures</span>
                <input type="checkbox" defaultChecked className="rounded" />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-white/80">System alerts</span>
                <input type="checkbox" defaultChecked className="rounded" />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )

  const renderLoggingSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">Logging Settings</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-white/80 mb-2">Log Level</label>
            <select 
              value={settings.logLevel}
              onChange={(e) => handleSettingChange('logLevel', e.target.value)}
              className="input-glass w-full"
            >
              <option value="debug">Debug</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm text-white/80 mb-2">Max Log File Size (MB)</label>
            <input 
              type="number"
              value={settings.maxLogSize}
              onChange={(e) => handleSettingChange('maxLogSize', e.target.value)}
              className="input-glass w-full"
              min="10"
              max="1000"
            />
          </div>

          <div className="glass p-4 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-white/80">Current Log Size</span>
              <span className="text-sm text-white">45.2 MB</span>
            </div>
            <div className="w-full bg-white/10 rounded-full h-2">
              <div className="bg-blue-400 h-2 rounded-full w-[45%]"></div>
            </div>
            <div className="flex justify-between text-xs text-white/60 mt-1">
              <span>0 MB</span>
              <span>100 MB</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  const renderAdvancedSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">Advanced Settings</h3>
        <div className="space-y-4">
          <div className="glass p-4 rounded-lg border-l-4 border-red-500">
            <div className="flex items-center space-x-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <span className="text-sm text-white/80">Danger Zone</span>
            </div>
            <div className="space-y-3">
              <button className="btn-secondary text-red-400 hover:text-red-300 w-full">
                Reset All Settings
              </button>
              <button className="btn-secondary text-red-400 hover:text-red-300 w-full">
                Clear All Data
              </button>
              <button className="btn-secondary text-red-400 hover:text-red-300 w-full">
                Factory Reset
              </button>
            </div>
          </div>

          <div className="glass p-4 rounded-lg">
            <h4 className="text-sm font-medium text-white mb-3">System Information</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-white/60">UI Version</span>
                <span className="text-white">1.0.0-alpha</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/60">Backend Version</span>
                <span className="text-white">1.0.0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/60">Build Date</span>
                <span className="text-white">2024-01-15</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  const renderTabContent = () => {
    switch (activeTab) {
      case 'general': return renderGeneralSettings()
      case 'connection': return renderConnectionSettings()
      case 'security': return renderSecuritySettings()
      case 'notifications': return renderNotificationSettings()
      case 'logging': return renderLoggingSettings()
      case 'advanced': return renderAdvancedSettings()
      default: return renderGeneralSettings()
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Settings</h2>
          <p className="text-white/60 mt-1">Configure your Anvyl installation</p>
        </div>
        <div className="flex space-x-3">
          <button className="btn-secondary flex items-center space-x-2">
            <RefreshCw className="w-4 h-4" />
            <span>Reset</span>
          </button>
          <button className="btn-primary flex items-center space-x-2">
            <Save className="w-4 h-4" />
            <span>Save Changes</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <nav className="space-y-1">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-all duration-200 ${
                    activeTab === tab.id 
                      ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30' 
                      : 'text-white/80 hover:text-white hover:bg-white/10'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-sm font-medium">{tab.name}</span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* Content */}
        <div className="lg:col-span-3">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="card"
          >
            {renderTabContent()}
          </motion.div>
        </div>
      </div>
    </div>
  )
}

export default SettingsView