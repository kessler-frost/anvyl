import React, { useState, useEffect } from 'react'
import {
  LayoutDashboard,
  Server,
  Container,
  Settings,
  Menu,
  X,
  Search,
  Activity,
  Plus,
  MoreHorizontal,
  Play,
  Square,
  Trash2,
  Edit
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { NavigationMenu, NavigationMenuContent, NavigationMenuItem, NavigationMenuLink, NavigationMenuList, NavigationMenuTrigger } from '@/components/ui/navigation-menu'

const navigation = [
  { name: 'Dashboard', icon: LayoutDashboard, id: 'dashboard' },
  { name: 'Hosts', icon: Server, id: 'hosts' },
  { name: 'Containers', icon: Container, id: 'containers' },
  { name: 'Settings', icon: Settings, id: 'settings' },
]

const stats = [
  {
    name: 'Total Hosts',
    value: '3',
    change: '+1',
    trend: 'up',
    icon: Server,
    color: 'text-gray-900'
  },
  {
    name: 'Containers',
    value: '12',
    change: '+3',
    trend: 'up',
    icon: Container,
    color: 'text-gray-900'
  },
  {
    name: 'System Load',
    value: '23%',
    change: '-5%',
    trend: 'down',
    icon: Activity,
    color: 'text-gray-900'
  }
]

const recentActivity = [
  { type: 'container', action: 'Created container nginx-web', time: '2 minutes ago', status: 'success' },
  { type: 'host', action: 'Mac Studio came online', time: '5 minutes ago', status: 'success' },
  { type: 'container', action: 'Container postgres-db stopped', time: '15 minutes ago', status: 'warning' }
]

function App() {
  const [activeView, setActiveView] = useState('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // Force dark mode for Apple-style dark theme
  useEffect(() => {
    document.documentElement.classList.add('dark')
  }, [])

  const renderView = () => {
    switch (activeView) {
      case 'dashboard':
        return <Dashboard />
      case 'hosts':
        return <HostsView />
      case 'containers':
        return <ContainersView />
      case 'settings':
        return <SettingsView />
      default:
        return <Dashboard />
    }
  }

  return (
    <div className="min-h-screen apple-gradient-dark">
      {/* Mobile sidebar */}
      <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
        <SheetContent side="left" className="w-80 p-0 apple-glass-dark">
          <Sidebar activeView={activeView} setActiveView={setActiveView} onClose={() => setSidebarOpen(false)} />
        </SheetContent>
      </Sheet>

      <div className="flex">
        {/* Desktop sidebar */}
        <aside className="hidden lg:flex w-80 flex-col fixed inset-y-0 z-50">
          <Sidebar activeView={activeView} setActiveView={setActiveView} />
        </aside>

        {/* Main content */}
        <div className="lg:pl-80 flex-1">
          {/* Header */}
          <header className="sticky top-0 z-40 border-b border-gray-700/50 apple-glass-dark backdrop-blur-xl">
            <div className="flex h-16 items-center gap-4 px-6">
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="ghost" size="icon" className="lg:hidden hover:bg-gray-800">
                    <Menu className="h-5 w-5" />
                  </Button>
                </SheetTrigger>
              </Sheet>

              <div className="flex-1">
                <h1 className="text-xl font-semibold capitalize text-white">{activeView}</h1>
              </div>

              <div className="flex items-center gap-4">
                <div className="relative">
                  <Search className="absolute left-4 top-3 h-4 w-4 text-gray-400" />
                  <Input placeholder="Search..." className="pl-10 w-64 input-apple-dark" />
                </div>

                <Avatar className="ring-2 ring-gray-700">
                  <AvatarImage src="/avatars/01.png" />
                  <AvatarFallback className="bg-gray-800 text-white">AN</AvatarFallback>
                </Avatar>
              </div>
            </div>
          </header>

          {/* Main content area */}
          <main className="flex-1 p-6">
            {renderView()}
          </main>
        </div>
      </div>
    </div>
  )
}

function Sidebar({ activeView, setActiveView, onClose }: {
  activeView: string,
  setActiveView: (view: string) => void,
  onClose?: () => void
}) {
  return (
    <div className="flex flex-col h-full apple-glass-dark">
      {/* Header */}
      <div className="flex flex-col items-center border-b border-gray-700/50 p-0">
        <div className="w-64 relative">
          <img
            src="/anvyl-logo.svg"
            alt="Anvyl Logo"
            className="w-full h-auto filter brightness-0 invert"
          />
        </div>
        {onClose && (
          <Button variant="ghost" size="icon" onClick={onClose} className="absolute top-4 right-4 hover:bg-gray-800">
            <X className="w-4 h-4" />
          </Button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-6 space-y-2">
        {navigation.map((item) => {
          const Icon = item.icon
          return (
            <Button
              key={item.id}
              variant={activeView === item.id ? "secondary" : "ghost"}
              className={`w-full justify-start transition-all duration-200 ${
                activeView === item.id
                  ? 'nav-item-dark active-dark'
                  : 'nav-item-dark'
              }`}
              onClick={() => {
                setActiveView(item.id)
                onClose?.()
              }}
            >
              <Icon className="w-5 h-5 mr-3" />
              {item.name}
            </Button>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-6 border-t border-gray-700/50">
        <Card className="apple-card-dark">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-white">Connected</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function Dashboard() {
  return (
    <div className="space-y-8">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.name} className="apple-card-dark">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-400">{stat.name}</p>
                    <p className="text-2xl font-bold text-white">{stat.value}</p>
                    <div className="flex items-center mt-2">
                      <span className={`text-sm font-medium ${
                        stat.trend === 'up' ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {stat.change}
                      </span>
                      <span className="text-sm text-gray-400 ml-1">from last month</span>
                    </div>
                  </div>
                  <Icon className={`w-8 h-8 ${stat.color}`} />
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Recent Activity */}
      <Card className="apple-card-dark">
        <CardHeader>
          <CardTitle className="text-white">Recent Activity</CardTitle>
          <CardDescription className="text-gray-400">Latest system events and actions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentActivity.map((activity, index) => (
              <div key={index} className="flex items-center justify-between p-4 rounded-lg bg-gray-800/50">
                <div className="flex items-center space-x-4">
                  <div className={`w-2 h-2 rounded-full ${
                    activity.status === 'success' ? 'bg-green-400' : 'bg-yellow-400'
                  }`} />
                  <div>
                    <p className="text-sm font-medium text-white">{activity.action}</p>
                    <p className="text-xs text-gray-400">{activity.time}</p>
                  </div>
                </div>
                <Badge variant={activity.status === 'success' ? 'default' : 'secondary'}>
                  {activity.type}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function HostsView() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Hosts</h2>
          <p className="text-gray-400">Manage your infrastructure hosts</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700">
          <Plus className="w-4 h-4 mr-2" />
          Add Host
        </Button>
      </div>

      <Card className="apple-card-dark">
        <CardHeader>
          <CardTitle className="text-xl font-semibold text-white">System Hosts</CardTitle>
          <CardDescription className="text-gray-400">All registered hosts in your network</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-gray-400">Host management interface coming soon...</p>
        </CardContent>
      </Card>
    </div>
  )
}

function ContainersView() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Containers</h2>
          <p className="text-gray-400">Manage Docker containers</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700">
          <Plus className="w-4 h-4 mr-2" />
          Create Container
        </Button>
      </div>

      <Card className="apple-card-dark">
        <CardHeader>
          <CardTitle className="text-xl font-semibold text-white">Running Containers</CardTitle>
          <CardDescription className="text-gray-400">All containers in your infrastructure</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-gray-400">Container management interface coming soon...</p>
        </CardContent>
      </Card>
    </div>
  )
}

function SettingsView() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-white">Settings</h2>
        <p className="text-gray-400">Configure your Anvyl instance</p>
      </div>

      <Card className="apple-card-dark">
        <CardHeader>
          <CardTitle className="text-xl font-semibold text-white">System Settings</CardTitle>
          <CardDescription className="text-gray-400">Configure system preferences and connections</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-gray-400">Settings interface coming soon...</p>
        </CardContent>
      </Card>
    </div>
  )
}

export default App
