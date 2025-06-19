import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Plus, 
  Server, 
  Cpu, 
  MemoryStick, 
  HardDrive, 
  Wifi,
  Settings,
  MoreVertical,
  Monitor
} from 'lucide-react'

const mockHosts = [
  {
    id: 'host-1',
    name: 'Mac Mini Server',
    ip: '192.168.1.100',
    os: 'macOS 15.0',
    status: 'online',
    cpu: { cores: 8, usage: 45 },
    memory: { total: 16, used: 9.6 },
    disk: { total: 512, used: 123 },
    containers: 4,
    agents: 2,
    lastSeen: '2 minutes ago'
  },
  {
    id: 'host-2',
    name: 'MacBook Pro Dev',
    ip: '192.168.1.101',
    os: 'macOS 15.0',
    status: 'online',
    cpu: { cores: 10, usage: 23 },
    memory: { total: 32, used: 12.8 },
    disk: { total: 1024, used: 456 },
    containers: 6,
    agents: 1,
    lastSeen: 'Just now'
  },
  {
    id: 'host-3',
    name: 'Mac Studio Build',
    ip: '192.168.1.102',
    os: 'macOS 15.0',
    status: 'offline',
    cpu: { cores: 20, usage: 0 },
    memory: { total: 64, used: 0 },
    disk: { total: 2048, used: 789 },
    containers: 0,
    agents: 0,
    lastSeen: '1 hour ago'
  }
]

const HostsView = () => {
  const [showAddModal, setShowAddModal] = useState(false)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'status-online'
      case 'offline': return 'status-offline'
      default: return 'status-offline'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Infrastructure Hosts</h2>
          <p className="text-white/60 mt-1">Manage your macOS hosts and their resources</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="btn-primary flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>Add Host</span>
        </button>
      </div>

      {/* Hosts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {mockHosts.map((host, index) => (
          <motion.div
            key={host.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="card glass-hover"
          >
            {/* Host Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-blue-600 rounded-lg flex items-center justify-center">
                  <Monitor className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-white">{host.name}</h3>
                  <p className="text-sm text-white/60">{host.ip}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(host.status)}`}>
                  {host.status}
                </span>
                <button className="p-1 hover:bg-white/10 rounded-md transition-colors">
                  <MoreVertical className="w-4 h-4 text-white/60" />
                </button>
              </div>
            </div>

            {/* System Info */}
            <div className="space-y-3 mb-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-white/60">OS Version</span>
                <span className="text-white">{host.os}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-white/60">Last Seen</span>
                <span className="text-white">{host.lastSeen}</span>
              </div>
            </div>

            {/* Resources */}
            <div className="space-y-4">
              {/* CPU */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Cpu className="w-4 h-4 text-blue-400" />
                    <span className="text-sm text-white/80">CPU</span>
                  </div>
                  <span className="text-sm text-white">{host.cpu.usage}%</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2">
                  <div 
                    className="bg-blue-400 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${host.cpu.usage}%` }}
                  />
                </div>
                <div className="text-xs text-white/60">{host.cpu.cores} cores</div>
              </div>

              {/* Memory */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <MemoryStick className="w-4 h-4 text-green-400" />
                    <span className="text-sm text-white/80">Memory</span>
                  </div>
                  <span className="text-sm text-white">
                    {host.memory.used}GB / {host.memory.total}GB
                  </span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2">
                  <div 
                    className="bg-green-400 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${(host.memory.used / host.memory.total) * 100}%` }}
                  />
                </div>
              </div>

              {/* Disk */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <HardDrive className="w-4 h-4 text-orange-400" />
                    <span className="text-sm text-white/80">Storage</span>
                  </div>
                  <span className="text-sm text-white">
                    {host.disk.used}GB / {host.disk.total}GB
                  </span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2">
                  <div 
                    className="bg-orange-400 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${(host.disk.used / host.disk.total) * 100}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Workload */}
            <div className="mt-4 pt-4 border-t border-white/10">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <div className="text-lg font-bold text-white">{host.containers}</div>
                  <div className="text-xs text-white/60">Containers</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-white">{host.agents}</div>
                  <div className="text-xs text-white/60">Agents</div>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="mt-4 flex space-x-2">
              <button className="btn-secondary flex-1 text-sm">
                <Settings className="w-4 h-4 mr-1" />
                Configure
              </button>
              <button className="btn-secondary flex-1 text-sm">
                <Wifi className="w-4 h-4 mr-1" />
                Connect
              </button>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Add Host Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setShowAddModal(false)} />
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card w-full max-w-md relative z-10"
          >
            <h3 className="text-lg font-semibold text-white mb-4">Add New Host</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-white/80 mb-2">Host Name</label>
                <input 
                  type="text" 
                  className="input-glass w-full" 
                  placeholder="e.g., Mac Studio Production"
                />
              </div>
              <div>
                <label className="block text-sm text-white/80 mb-2">IP Address</label>
                <input 
                  type="text" 
                  className="input-glass w-full" 
                  placeholder="e.g., 192.168.1.103"
                />
              </div>
              <div>
                <label className="block text-sm text-white/80 mb-2">OS Version</label>
                <input 
                  type="text" 
                  className="input-glass w-full" 
                  placeholder="e.g., macOS 15.0"
                />
              </div>
              <div className="flex space-x-3 mt-6">
                <button 
                  onClick={() => setShowAddModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button className="btn-primary flex-1">Add Host</button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}

export default HostsView