import { motion } from 'framer-motion'
import { 
  Server, 
  Container, 
  Bot, 
  Activity, 
  Cpu, 
  HardDrive, 
  MemoryStick,
  TrendingUp
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

const stats = [
  {
    name: 'Total Hosts',
    value: '3',
    change: '+1',
    trend: 'up',
    icon: Server,
    color: 'from-blue-400 to-blue-600'
  },
  {
    name: 'Containers',
    value: '12',
    change: '+3',
    trend: 'up',
    icon: Container,
    color: 'from-green-400 to-green-600'
  },
  {
    name: 'Agents',
    value: '5',
    change: '+2',
    trend: 'up',
    icon: Bot,
    color: 'from-purple-400 to-purple-600'
  },
  {
    name: 'System Load',
    value: '23%',
    change: '-5%',
    trend: 'down',
    icon: Activity,
    color: 'from-orange-400 to-orange-600'
  }
]

const containerData = [
  { name: 'Running', value: 8, color: '#10b981' },
  { name: 'Stopped', value: 3, color: '#ef4444' },
  { name: 'Building', value: 1, color: '#f59e0b' }
]

const hostsData = [
  { name: 'Mac Mini', cpu: 45, memory: 62, disk: 78 },
  { name: 'MacBook Pro', cpu: 23, memory: 34, disk: 56 },
  { name: 'Mac Studio', cpu: 67, memory: 89, disk: 45 }
]

const Dashboard = () => {
  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <motion.div
              key={stat.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="card glass-hover cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-white/60">{stat.name}</p>
                  <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                  <div className="flex items-center mt-2">
                    <TrendingUp className={`w-4 h-4 mr-1 ${
                      stat.trend === 'up' ? 'text-green-400' : 'text-red-400'
                    }`} />
                    <span className={`text-sm ${
                      stat.trend === 'up' ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {stat.change}
                    </span>
                  </div>
                </div>
                <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${stat.color} flex items-center justify-center`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Container Status Chart */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="card"
        >
          <h3 className="text-lg font-semibold text-white mb-4">Container Status</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={containerData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {containerData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center space-x-4 mt-4">
            {containerData.map((entry) => (
              <div key={entry.name} className="flex items-center space-x-2">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-sm text-white/80">{entry.name}: {entry.value}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Host Resources Chart */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="card"
        >
          <h3 className="text-lg font-semibold text-white mb-4">Host Resources</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={hostsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis 
                  dataKey="name" 
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }}
                />
                <YAxis 
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }}
                />
                <Bar dataKey="cpu" fill="#3b82f6" radius={[2, 2, 0, 0]} />
                <Bar dataKey="memory" fill="#10b981" radius={[2, 2, 0, 0]} />
                <Bar dataKey="disk" fill="#f59e0b" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center space-x-4 mt-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-blue-500" />
              <span className="text-sm text-white/80">CPU</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span className="text-sm text-white/80">Memory</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-yellow-500" />
              <span className="text-sm text-white/80">Disk</span>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Recent Activity */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="card"
      >
        <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
        <div className="space-y-3">
          {[
            { type: 'container', action: 'Created container nginx-web', time: '2 minutes ago', status: 'success' },
            { type: 'host', action: 'Mac Studio came online', time: '5 minutes ago', status: 'success' },
            { type: 'agent', action: 'Backup agent started on Mac Mini', time: '10 minutes ago', status: 'success' },
            { type: 'container', action: 'Container postgres-db stopped', time: '15 minutes ago', status: 'warning' }
          ].map((activity, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 + index * 0.1 }}
              className="flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
            >
              <div className="flex items-center space-x-3">
                <div className={`w-2 h-2 rounded-full ${
                  activity.status === 'success' ? 'bg-green-400' : 'bg-yellow-400'
                }`} />
                <span className="text-white/80">{activity.action}</span>
              </div>
              <span className="text-sm text-white/60">{activity.time}</span>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  )
}

export default Dashboard