import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  LayoutDashboard, 
  Server, 
  Container, 
  Bot, 
  Settings, 
  Menu,
  X,
  Activity
} from 'lucide-react'
import Dashboard from './components/Dashboard'
import HostsView from './components/HostsView'
import ContainersView from './components/ContainersView'
import AgentsView from './components/AgentsView'
import SettingsView from './components/SettingsView'

const navigation = [
  { name: 'Dashboard', icon: LayoutDashboard, id: 'dashboard' },
  { name: 'Hosts', icon: Server, id: 'hosts' },
  { name: 'Containers', icon: Container, id: 'containers' },
  { name: 'Agents', icon: Bot, id: 'agents' },
  { name: 'Settings', icon: Settings, id: 'settings' },
]

function App() {
  const [activeView, setActiveView] = useState('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const renderView = () => {
    switch (activeView) {
      case 'dashboard':
        return <Dashboard />
      case 'hosts':
        return <HostsView />
      case 'containers':
        return <ContainersView />
      case 'agents':
        return <AgentsView />
      case 'settings':
        return <SettingsView />
      default:
        return <Dashboard />
    }
  }

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Mobile sidebar overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          >
            <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        initial={{ x: -280 }}
        animate={{ x: sidebarOpen ? 0 : -280 }}
        className="fixed lg:static inset-y-0 left-0 z-50 w-64 lg:translate-x-0 transition-transform duration-300 ease-in-out lg:duration-0"
      >
        <div className="flex flex-col h-full glass border-r border-white/10">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-white/10">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-primary-400 to-primary-600 rounded-lg flex items-center justify-center">
                <Activity className="w-4 h-4 text-white" />
              </div>
              <h1 className="text-xl font-bold text-white">Anvyl</h1>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-1 rounded-md hover:bg-white/10 transition-colors"
            >
              <X className="w-5 h-5 text-white" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveView(item.id)
                    setSidebarOpen(false)
                  }}
                  className={`nav-item w-full ${
                    activeView === item.id ? 'active' : ''
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </button>
              )
            })}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-white/10">
            <div className="glass-hover rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm text-white/80">Connected</span>
              </div>
              <p className="text-xs text-white/60 mt-1">localhost:50051</p>
            </div>
          </div>
        </div>
      </motion.aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="glass border-b border-white/10 px-6 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-md hover:bg-white/10 transition-colors"
            >
              <Menu className="w-5 h-5 text-white" />
            </button>
            
            <h2 className="text-2xl font-semibold text-white capitalize">
              {activeView}
            </h2>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-white/80">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span>System Healthy</span>
              </div>
            </div>
          </div>
        </header>

        {/* Main content area */}
        <main className="flex-1 overflow-auto p-6">
          <motion.div
            key={activeView}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="h-full"
          >
            {renderView()}
          </motion.div>
        </main>
      </div>
    </div>
  )
}

export default App
