import { useState, useEffect } from 'react'
import {
  LayoutDashboard,
  Server,
  Container,
  Bot,
  Settings,
  Menu,
  X,
  Activity,
  Users,
  Database,
  Network,
  BarChart3,
  Plus,
  Search
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
  { name: 'Agents', icon: Bot, id: 'agents' },
  { name: 'Settings', icon: Settings, id: 'settings' },
]

const stats = [
  {
    name: 'Total Hosts',
    value: '3',
    change: '+1',
    trend: 'up',
    icon: Server,
    color: 'text-blue-600'
  },
  {
    name: 'Containers',
    value: '12',
    change: '+3',
    trend: 'up',
    icon: Container,
    color: 'text-green-600'
  },
  {
    name: 'Agents',
    value: '5',
    change: '+2',
    trend: 'up',
    icon: Bot,
    color: 'text-purple-600'
  },
  {
    name: 'System Load',
    value: '23%',
    change: '-5%',
    trend: 'down',
    icon: Activity,
    color: 'text-orange-600'
  }
]

const recentActivity = [
  { type: 'container', action: 'Created container nginx-web', time: '2 minutes ago', status: 'success' },
  { type: 'host', action: 'Mac Studio came online', time: '5 minutes ago', status: 'success' },
  { type: 'agent', action: 'Backup agent started on Mac Mini', time: '10 minutes ago', status: 'success' },
  { type: 'container', action: 'Container postgres-db stopped', time: '15 minutes ago', status: 'warning' }
]

function App() {
  const [activeView, setActiveView] = useState('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // Force dark mode
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
      case 'agents':
        return <AgentsView />
      case 'settings':
        return <SettingsView />
      default:
        return <Dashboard />
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile sidebar */}
      <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
        <SheetContent side="left" className="w-64 p-0">
          <Sidebar activeView={activeView} setActiveView={setActiveView} onClose={() => setSidebarOpen(false)} />
        </SheetContent>
      </Sheet>

      <div className="flex">
        {/* Desktop sidebar */}
        <aside className="hidden lg:flex w-64 flex-col fixed inset-y-0 z-50">
          <Sidebar activeView={activeView} setActiveView={setActiveView} />
        </aside>

        {/* Main content */}
        <div className="lg:pl-64 flex-1">
          {/* Header */}
          <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="flex h-16 items-center gap-4 px-4 sm:px-6">
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="ghost" size="icon" className="lg:hidden">
                    <Menu className="h-5 w-5" />
                  </Button>
                </SheetTrigger>
              </Sheet>

              <div className="flex-1">
                <h1 className="text-lg font-semibold capitalize">{activeView}</h1>
              </div>

              <div className="flex items-center gap-4">
                <div className="relative">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input placeholder="Search..." className="pl-8 w-64" />
                </div>

                <Avatar>
                  <AvatarImage src="/avatars/01.png" />
                  <AvatarFallback>AN</AvatarFallback>
                </Avatar>
              </div>
            </div>
          </header>

          {/* Main content area */}
          <main className="flex-1 p-4 sm:p-6">
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
    <div className="flex flex-col h-full bg-card border-r">
      {/* Header */}
      <div className="flex flex-col items-center border-b">
        <div className="w-[280px] relative">
          <img
            src="/anvyl-logo.svg"
            alt="Anvyl Logo"
            className="w-full h-auto"
          />
        </div>
        {onClose && (
          <Button variant="ghost" size="icon" onClick={onClose} className="absolute top-2 right-2">
            <X className="w-4 h-4" />
          </Button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => {
          const Icon = item.icon
          return (
            <Button
              key={item.id}
              variant={activeView === item.id ? "secondary" : "ghost"}
              className="w-full justify-start"
              onClick={() => {
                setActiveView(item.id)
                onClose?.()
              }}
            >
              <Icon className="w-4 h-4 mr-2" />
              {item.name}
            </Button>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t">
        <Card>
          <CardContent className="p-3">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium">Connected</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function Dashboard() {
  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <Card key={stat.name}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{stat.name}</CardTitle>
                <Icon className={`w-4 h-4 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className={`text-xs ${stat.trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                  {stat.change} from last month
                </p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Latest system events and actions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentActivity.map((activity, index) => (
              <div key={index} className="flex items-center gap-4">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium">{activity.action}</p>
                  <p className="text-xs text-muted-foreground">{activity.time}</p>
                </div>
                <Badge variant={activity.status === 'success' ? 'default' : 'secondary'}>
                  {activity.status}
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
        <h2 className="text-3xl font-bold tracking-tight">Hosts</h2>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          Add Host
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>System Hosts</CardTitle>
          <CardDescription>Manage your infrastructure hosts</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">Host management interface coming soon...</p>
        </CardContent>
      </Card>
    </div>
  )
}

function ContainersView() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Containers</h2>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          Create Container
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Docker Containers</CardTitle>
          <CardDescription>Manage your containerized applications</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">Container management interface coming soon...</p>
        </CardContent>
      </Card>
    </div>
  )
}

function AgentsView() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Agents</h2>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          Launch Agent
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>System Agents</CardTitle>
          <CardDescription>Manage automated agents and tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">Agent management interface coming soon...</p>
        </CardContent>
      </Card>
    </div>
  )
}

function SettingsView() {
  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
      <Card>
        <CardHeader>
          <CardTitle>System Configuration</CardTitle>
          <CardDescription>Configure your Anvyl instance</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">Settings interface coming soon...</p>
        </CardContent>
      </Card>
    </div>
  )
}

export default App
