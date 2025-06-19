import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Plus, 
  Bot, 
  Play, 
  Square, 
  Trash2,
  MoreVertical,
  Clock,
  FileText,
  Zap,
  Activity
} from 'lucide-react'

const mockAgents = [
  {
    id: 'agent-1',
    name: 'backup-service',
    type: 'Backup Agent',
    host: 'Mac Mini Server',
    status: 'running',
    entrypoint: '/usr/local/bin/backup.py',
    workingDir: '/opt/backup',
    persistent: true,
    created: '1 day ago',
    uptime: '1d 12h 30m',
    lastExecution: '30 minutes ago',
    executions: 48,
    cpu: 5,
    memory: 32
  },
  {
    id: 'agent-2',
    name: 'log-collector',
    type: 'Monitoring Agent',
    host: 'MacBook Pro Dev',
    status: 'running',
    entrypoint: '/usr/local/bin/collect_logs.sh',
    workingDir: '/var/log',
    persistent: true,
    created: '3 days ago',
    uptime: '3d 8h 15m',
    lastExecution: '5 minutes ago',
    executions: 144,
    cpu: 2,
    memory: 16
  },
  {
    id: 'agent-3',
    name: 'deployment-worker',
    type: 'CI/CD Agent',
    host: 'Mac Studio Build',
    status: 'stopped',
    entrypoint: '/usr/local/bin/deploy.py',
    workingDir: '/opt/deploy',
    persistent: false,
    created: '2 hours ago',
    uptime: '0s',
    lastExecution: 'Never',
    executions: 0,
    cpu: 0,
    memory: 0
  },
  {
    id: 'agent-4',
    name: 'health-checker',
    type: 'Health Agent',
    host: 'Mac Mini Server',
    status: 'error',
    entrypoint: '/usr/local/bin/health_check.py',
    workingDir: '/opt/health',
    persistent: true,
    created: '5 days ago',
    uptime: '0s',
    lastExecution: '2 hours ago',
    executions: 240,
    cpu: 0,
    memory: 0
  }
]

const AgentsView = () => {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [filter, setFilter] = useState('all')

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'status-running'
      case 'stopped': return 'status-stopped'
      case 'error': return 'bg-red-500/20 text-red-300 border-red-500/30'
      default: return 'status-stopped'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <Play className="w-3 h-3" />
      case 'stopped': return <Square className="w-3 h-3" />
      case 'error': return <Zap className="w-3 h-3" />
      default: return <Square className="w-3 h-3" />
    }
  }

  const filteredAgents = mockAgents.filter(agent => {
    if (filter === 'all') return true
    return agent.status === filter
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Agent Management</h2>
          <p className="text-white/60 mt-1">Deploy and manage background agents across your infrastructure</p>
        </div>
        <div className="flex items-center space-x-3">
          {/* Filter */}
          <select 
            value={filter} 
            onChange={(e) => setFilter(e.target.value)}
            className="input-glass px-3 py-2"
          >
            <option value="all">All Agents</option>
            <option value="running">Running</option>
            <option value="stopped">Stopped</option>
            <option value="error">Error</option>
          </select>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Launch Agent</span>
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Total', value: mockAgents.length, color: 'from-purple-400 to-purple-600' },
          { label: 'Running', value: mockAgents.filter(a => a.status === 'running').length, color: 'from-green-400 to-green-600' },
          { label: 'Stopped', value: mockAgents.filter(a => a.status === 'stopped').length, color: 'from-red-400 to-red-600' },
          { label: 'Errors', value: mockAgents.filter(a => a.status === 'error').length, color: 'from-orange-400 to-orange-600' }
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
                <Bot className="w-5 h-5 text-white" />
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {filteredAgents.map((agent, index) => (
          <motion.div
            key={agent.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="card glass-hover"
          >
            {/* Agent Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-indigo-400 to-indigo-600 rounded-lg flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-white">{agent.name}</h3>
                  <p className="text-sm text-white/60">{agent.type}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`px-2 py-1 rounded-full text-xs font-medium border flex items-center space-x-1 ${getStatusColor(agent.status)}`}>
                  {getStatusIcon(agent.status)}
                  <span>{agent.status}</span>
                </span>
                {agent.persistent && (
                  <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-500/20 text-blue-300 border border-blue-500/30">
                    Persistent
                  </span>
                )}
                <button className="p-1 hover:bg-white/10 rounded-md transition-colors">
                  <MoreVertical className="w-4 h-4 text-white/60" />
                </button>
              </div>
            </div>

            {/* Agent Info */}
            <div className="space-y-3 mb-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-white/60">Host</span>
                <span className="text-white">{agent.host}</span>
              </div>
              <div className="flex items-start justify-between text-sm">
                <span className="text-white/60">Entrypoint</span>
                <span className="text-white text-right font-mono text-xs">{agent.entrypoint}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-white/60">Working Dir</span>
                <span className="text-white font-mono text-xs">{agent.workingDir}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-white/60">Created</span>
                <span className="text-white">{agent.created}</span>
              </div>
              {agent.status === 'running' && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-white/60">Uptime</span>
                  <span className="text-white">{agent.uptime}</span>
                </div>
              )}
            </div>

            {/* Execution Stats */}
            <div className="space-y-3 mb-4 p-3 rounded-lg bg-white/5">
              <div className="flex items-center justify-between text-sm">
                <span className="text-white/60 flex items-center space-x-1">
                  <Activity className="w-3 h-3" />
                  <span>Executions</span>
                </span>
                <span className="text-white">{agent.executions}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-white/60 flex items-center space-x-1">
                  <Clock className="w-3 h-3" />
                  <span>Last Run</span>
                </span>
                <span className="text-white">{agent.lastExecution}</span>
              </div>
              
              {agent.status === 'running' && (
                <>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-white/60">CPU Usage</span>
                    <span className="text-white">{agent.cpu}%</span>
                  </div>
                  <div className="w-full bg-white/10 rounded-full h-1.5">
                    <div 
                      className="bg-purple-400 h-1.5 rounded-full transition-all duration-300"
                      style={{ width: `${agent.cpu}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-white/60">Memory</span>
                    <span className="text-white">{agent.memory} MB</span>
                  </div>
                </>
              )}
            </div>

            {/* Actions */}
            <div className="flex space-x-2">
              {agent.status === 'running' ? (
                <>
                  <button className="btn-secondary flex-1 text-sm">
                    <Square className="w-3 h-3 mr-1" />
                    Stop
                  </button>
                  <button className="btn-secondary px-3">
                    <FileText className="w-4 h-4" />
                  </button>
                </>
              ) : (
                <>
                  <button className="btn-primary flex-1 text-sm">
                    <Play className="w-3 h-3 mr-1" />
                    Start
                  </button>
                  <button className="btn-secondary px-3">
                    <FileText className="w-4 h-4" />
                  </button>
                  <button className="btn-secondary px-3 text-red-400 hover:text-red-300">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </>
              )}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Create Agent Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setShowCreateModal(false)} />
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card w-full max-w-lg relative z-10"
          >
            <h3 className="text-lg font-semibold text-white mb-4">Launch New Agent</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-white/80 mb-2">Agent Name</label>
                <input 
                  type="text" 
                  className="input-glass w-full" 
                  placeholder="e.g., backup-service"
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
                <label className="block text-sm text-white/80 mb-2">Entrypoint Script</label>
                <input 
                  type="text" 
                  className="input-glass w-full" 
                  placeholder="/usr/local/bin/my_agent.py"
                />
              </div>
              <div>
                <label className="block text-sm text-white/80 mb-2">Working Directory</label>
                <input 
                  type="text" 
                  className="input-glass w-full" 
                  placeholder="/opt/agent"
                />
              </div>
              <div>
                <label className="block text-sm text-white/80 mb-2">Arguments</label>
                <input 
                  type="text" 
                  className="input-glass w-full" 
                  placeholder="--config /etc/agent.conf"
                />
              </div>
              <div className="flex items-center space-x-2">
                <input 
                  type="checkbox" 
                  id="persistent"
                  className="rounded border-white/20 bg-white/10 text-primary-500 focus:ring-primary-500 focus:ring-offset-0"
                />
                <label htmlFor="persistent" className="text-sm text-white/80">
                  Make agent persistent (restart on failure)
                </label>
              </div>
              <div className="flex space-x-3 mt-6">
                <button 
                  onClick={() => setShowCreateModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button className="btn-primary flex-1">Launch Agent</button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}

export default AgentsView