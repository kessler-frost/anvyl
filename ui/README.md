# Anvyl UI - Komodo Inspired Interface

A modern, beautiful web interface for Anvyl infrastructure orchestrator, inspired by [Komodo Digital's](https://www.komododigital.co.uk/) design principles.

## 🎨 Design Philosophy

This UI is inspired by Komodo's approach to modern web design:

- **Glassmorphism Effects**: Semi-transparent elements with backdrop blur for a modern, layered look
- **Dark Theme First**: Beautiful dark gradient backgrounds with subtle lighting
- **Minimalist & Clean**: Focus on essential elements, ample white space, clear hierarchy
- **Mobile-First Responsive**: Works beautifully on all devices
- **Smooth Animations**: Framer Motion powered transitions and micro-interactions
- **Accessibility Focused**: Proper contrast ratios, keyboard navigation, screen reader support
- **User-Centered Design**: Intuitive navigation and clear information architecture

## 🏗 Architecture

```
ui/
├── frontend/          # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/    # UI Components
│   │   │   ├── Dashboard.tsx      # System overview with charts
│   │   │   ├── HostsView.tsx      # macOS hosts management
│   │   │   ├── ContainersView.tsx # Docker container management
│   │   │   ├── AgentsView.tsx     # Background agents management
│   │   │   └── SettingsView.tsx   # System configuration
│   │   ├── hooks/         # Custom React hooks
│   │   ├── store/         # State management (Zustand)
│   │   └── types/         # TypeScript definitions
└── backend/           # FastAPI + gRPC bridge
    ├── main.py        # REST API server
    └── requirements.txt
```

## 🚀 Features

### Dashboard
- **System Overview**: Real-time stats with beautiful charts (Recharts)
- **Resource Monitoring**: Host CPU, memory, disk usage with animated progress bars
- **Activity Feed**: Recent system events with status indicators
- **Container Status**: Pie chart visualization of container states

### Host Management
- **Infrastructure View**: Beautiful cards showing each macOS host
- **Resource Visualization**: Real-time CPU, memory, storage with progress indicators
- **Host Actions**: Connect, configure, monitor individual hosts
- **Add New Hosts**: Modal form with glassmorphism styling

### Container Management
- **Container Grid**: Clean card layout with status indicators
- **Lifecycle Control**: Start, stop, restart containers with smooth animations
- **Resource Monitoring**: Real-time CPU/memory usage for running containers
- **Log Viewing**: Container logs with syntax highlighting
- **Creation Wizard**: Step-by-step container deployment

### Agent Management
- **Agent Overview**: Background service monitoring
- **Execution Tracking**: Run count, last execution, uptime statistics
- **Persistent Agents**: Visual indicators for always-running services
- **Launch Interface**: Easy agent deployment with configuration options

### Settings
- **Tabbed Interface**: Clean organization of configuration options
- **Connection Settings**: gRPC server configuration
- **Security Options**: Authentication and TLS settings
- **Notifications**: Customizable alert preferences
- **Theme Options**: Dark/light/auto theme switching

## 🎯 Design Elements

### Color Palette
- **Primary**: Blue gradient (#0ea5e9 to #0284c7) - Trust and reliability
- **Secondary**: Neutral grays with transparency - Modern and clean
- **Accent**: Gold (#eab308) - Highlights and success states
- **Status Colors**: Green (online/running), Red (offline/stopped), Orange (warning)

### Typography
- **Primary Font**: Inter - Clean, modern, highly readable
- **Monospace Font**: JetBrains Mono - For code and technical content
- **Hierarchy**: Clear size and weight distinctions for information hierarchy

### Layout & Spacing
- **Grid System**: CSS Grid and Flexbox for responsive layouts
- **Spacing Scale**: Consistent 4px base scale (4, 8, 12, 16, 24, 32px)
- **Border Radius**: 8px for cards, 4px for buttons, 6px for inputs
- **Glass Effects**: 10% white opacity with backdrop blur for depth

### Animations
- **Page Transitions**: Smooth fade-in with subtle slide-up motion
- **Hover States**: Gentle scale and glow effects
- **Loading States**: Skeleton animations and progress indicators
- **Microinteractions**: Button press feedback, toggle switches

## 🛠 Technology Stack

### Frontend
- **React 18** - Modern React with hooks and concurrent features
- **TypeScript** - Type-safe development with excellent tooling
- **Vite** - Fast build tool with hot module replacement
- **Tailwind CSS** - Utility-first CSS framework with custom design tokens
- **Framer Motion** - Smooth animations and transitions
- **Lucide React** - Beautiful, consistent icons
- **Recharts** - Responsive charts for data visualization
- **Zustand** - Lightweight state management
- **Axios** - HTTP client for API communication

### Backend
- **FastAPI** - Modern Python web framework
- **Pydantic** - Data validation and API documentation
- **gRPC Client** - Bridge to existing Anvyl infrastructure
- **CORS Support** - Cross-origin requests for development

## 📦 Setup & Installation

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+ (for backend)
- Running Anvyl gRPC server

### Frontend Development

```bash
cd ui/frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to see the interface.

### Backend API (Optional)

```bash
cd ui/backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

API available at `http://localhost:8000` with docs at `/docs`.

## 🎨 Design Inspiration

This interface draws inspiration from:

- **Komodo Digital's** modern, user-centered design approach
- **Glassmorphism** trend for depth and visual interest
- **Apple's Human Interface Guidelines** for clarity and usability
- **Material Design 3** for accessibility and responsive behavior
- **Figma** and **Linear** for clean, professional interfaces

## 🔮 Future Enhancements

- **Real-time Updates**: WebSocket integration for live data
- **Advanced Monitoring**: Custom dashboards and alerting
- **Multi-tenant Support**: User accounts and permissions
- **Mobile App**: React Native companion app
- **Theme Customization**: Custom color schemes and branding
- **Keyboard Shortcuts**: Power user productivity features

## 📝 Development Notes

### Component Structure
Each view component follows a consistent pattern:
- State management with React hooks
- Responsive grid layouts
- Consistent spacing and typography
- Accessible form controls
- Error handling and loading states

### Design Tokens
All design values are centralized in `tailwind.config.js`:
- Color schemes with opacity variants
- Typography scale and font families
- Spacing and sizing scales
- Animation presets and keyframes
- Custom shadows and effects

### Accessibility
- WCAG 2.1 AA compliance
- Keyboard navigation support
- Screen reader optimization
- High contrast mode support
- Focus visible indicators

---

Built with ❤️ inspired by Komodo Digital's design excellence.