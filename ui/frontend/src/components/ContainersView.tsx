import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Plus, 
  Container, 
  Play, 
  Square, 
  RotateCcw,
  Trash2,
  MoreVertical,
  Eye,
  Terminal,
  Clock,
  Zap
} from 'lucide-react'

const mockContainers = [
  {
    id: 'cont-1',
    name: 'nginx-web',
    image: 'nginx:alpine',
    status: 'running',
    host: 'Mac Mini Server',
    ports: ['8080:80', '8443:443'],
    created: '2 days ago',
    uptime: '2d 4h 12m',
    cpu: 12,
    memory: 64,
    network: { in: '2.3 MB', out: '1.8 MB' }
  },
  {
    id: 'cont-2',
    name: 'postgres-db',
    image: 'postgres:15',
    status: 'running',
    host: 'MacBook Pro Dev',
    ports: ['5432:5432'],
    created: '1 week ago',
    uptime: '7d 2h 45m',
    cpu: 8,
    memory: 256,
    network: { in: '5.1 MB', out: '3.2 MB' }
  },
  {
    id: 'cont-3',
    name: 'redis-cache',
    image: 'redis:7-alpine',
    status: 'stopped',
    host: 'Mac Studio Build',
    ports: ['6379:6379'],
    created: '3 days ago',
    uptime: '0s',
    cpu: 0,
    memory: 0,
    network: { in: '0 B', out: '0 B' }
  },
  {
    id: 'cont-4',
    name: 'monitoring',
    image: 'grafana/grafana:latest',
    status: 'building',
    host: 'Mac Mini Server',
    ports: ['3000:3000'],
    created: '5 minutes ago',
    uptime: '0s',
    cpu: 0,
    memory: 0,
    network: { in: '0 B', out: '0 B' }
  }
]

const ContainersView = () => {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [filter, setFilter] = useState('all')

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'status-running'
      case 'stopped': return 'status-stopped'
      case 'building': return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30'
      case 'error': return 'bg-red-500/20 text-red-300 border-red-500/30'
      default: return 'status-stopped'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <Play className="w-3 h-3" />
      case 'stopped': return <Square className="w-3 h-3" />
      case 'building': return <RotateCcw className="w-3 h-3 animate-spin" />
      default: return <Square className="w-3 h-3" />
    }
  }

  const filteredContainers = mockContainers.filter(container => {
    if (filter === 'all') return true
    return container.status === filter
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Container Management</h2>
          <p className="text-white/60 mt-1">Deploy and manage Docker containers across your infrastructure</p>
        </div>
        <div className="flex items-center space-x-3">
          {/* Filter */}
          <select 
            value={filter} 
            onChange={(e) => setFilter(e.target.value)}
            className="input-glass px-3 py-2"
          >
            <option value="all">All Containers</option>
            <option value="running">Running</option>
            <option value="stopped">Stopped</option>
            <option value="building">Building</option>
          </select>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Create Container</span>
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Total', value: mockContainers.length, color: 'from-blue-400 to-blue-600' },
          { label: 'Running', value: mockContainers.filter(c => c.status === 'running').length, color: 'from-green-400 to-green-600' },
          { label: 'Stopped', value: mockContainers.filter(c => c.status === 'stopped').length, color: 'from-red-400 to-red-600' },
          { label: 'Building', value: mockContainers.filter(c => c.status === 'building').length, color: 'from-yellow-400 to-yellow-600' }
        ].map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="glass rounded-lg p-4"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white/60">{stat.label}</p>
                <p className="text-2xl font-bold text-white">{stat.value}</p>
              </div>
              <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${stat.color} flex items-center justify-center`}>
                <Container className="w-5 h-5 text-white" />
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Containers Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {filteredContainers.map((container, index) => (
          <motion.div
            key={container.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="card glass-hover"
          >
            {/* Container Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-purple-400 to-purple-600 rounded-lg flex items-center justify-center">
                  <Container className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-white">{container.name}</h3>
                  <p className="text-sm text-white/60">{container.image}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`px-2 py-1 rounded-full text-xs font-medium border flex items-center space-x-1 ${getStatusColor(container.status)}`}>
                  {getStatusIcon(container.status)}
                  <span>{container.status}</span>
                </span>
                <button className="p-1 hover:bg-white/10 rounded-md transition-colors">
                  <MoreVertical className="w-4 h-4 text-white/60" />
                </button>
              </div>
            </div>

            {/* Container Info */}
            <div className="space-y-3 mb-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-white/60">Host</span>
                <span className="text-white">{container.host}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-white/60">Ports</span>
                <span className="text-white">{container.ports.join(', ')}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-white/60">Created</span>
                <span className="text-white">{container.created}</span>
              </div>
              {container.status === 'running' && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-white/60">Uptime</span>
                  <span className="text-white">{container.uptime}</span>
                </div>
              )}
            </div>

            {/* Resource Usage */}
            {container.status === 'running' && (
              <div className="space-y-3 mb-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-white/60 flex items-center space-x-1">
                    <Zap className="w-3 h-3" />
                    <span>CPU</span>
                  </span>
                  <span className="text-white">{container.cpu}%</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2">
                  <div 
                    className="bg-blue-400 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${container.cpu}%` }}
                  />
                </div>
                
                <div className="flex items-center justify-between text-sm">
                  <span className="text-white/60">Memory</span>
                  <span className="text-white">{container.memory} MB</span>
                </div>
                
                <div className="flex items-center justify-between text-sm">
                  <span className="text-white/60">Network</span>
                  <span className="text-white">↓{container.network.in} ↑{container.network.out}</span>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex space-x-2">
              {container.status === 'running' ? (
                <>
                  <button className="btn-secondary flex-1 text-sm">
                    <Square className="w-3 h-3 mr-1" />
                    Stop
                  </button>
                  <button className="btn-secondary px-3">
                    <Eye className="w-4 h-4" />
                  </button>
                  <button className="btn-secondary px-3">
                    <Terminal className="w-4 h-4" />
                  </button>
                </>
              ) : container.status === 'stopped' ? (
                <>
                  <button className="btn-primary flex-1 text-sm">
                    <Play className="w-3 h-3 mr-1" />
                    Start
                  </button>
                  <button className="btn-secondary px-3">
                    <Eye className="w-4 h-4" />
                  </button>
                  <button className="btn-secondary px-3 text-red-400 hover:text-red-300">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </>
              ) : (
                <button className="btn-secondary flex-1 text-sm">
                  <Clock className="w-3 h-3 mr-1" />
                  Building...
                </button>
              )}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Create Container Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setShowCreateModal(false)} />
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card w-full max-w-lg relative z-10"
          >
            <h3 className="text-lg font-semibold text-white mb-4">Create New Container</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-white/80 mb-2">Container Name</label>
                <input 
                  type="text" 
                  className="input-glass w-full" 
                  placeholder="e.g., my-web-app"
                />
              </div>
              <div>
                <label className="block text-sm text-white/80 mb-2">Docker Image</label>
                <input 
                  type="text" 
                  className="input-glass w-full" 
                  placeholder="e.g., nginx:alpine"
                />
              </div>
              <div>
                <label className="block text-sm text-white/80 mb-2">Target Host</label>
                <select className="input-glass w-full">
                  <option>Mac Mini Server</option>
                  <option>MacBook Pro Dev</option>
                  <option>Mac Studio Build</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-white/80 mb-2">Port Mapping</label>
                <input 
                  type="text" 
                  className="input-glass w-full" 
                  placeholder="e.g., 8080:80"
                />
              </div>
              <div>
                <label className="block text-sm text-white/80 mb-2">Environment Variables</label>
                <textarea 
                  className="input-glass w-full h-20 resize-none" 
                  placeholder="KEY=value (one per line)"
                />
              </div>
              <div className="flex space-x-3 mt-6">
                <button 
                  onClick={() => setShowCreateModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button className="btn-primary flex-1">Create Container</button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}

export default ContainersView