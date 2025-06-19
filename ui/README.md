# Anvyl UI - Modern Interface

A modern, beautiful web interface for Anvyl infrastructure orchestrator with contemporary design principles.

## 🎨 Design Philosophy

This UI embodies modern web design principles:

- **User-Centered Design**: Intuitive interfaces that prioritize user experience
- **Modern Aesthetics**: Clean lines, thoughtful spacing, and contemporary visual effects
- **Accessibility First**: Designed to be usable by everyone
- **Mobile-First**: Responsive design that works beautifully on all devices
- **Performance Focus**: Fast, efficient, and smooth interactions

## 🏗 Architecture

The UI consists of two main components:

- **Frontend**: React + TypeScript application with Tailwind CSS
- **Backend**: FastAPI server that bridges the React app with the Anvyl gRPC server

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
- Node.js 18+
- Python 3.12+
- Docker Desktop

### Local Development

```bash
# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies
cd ../backend
pip install -r requirements.txt

# Start backend development server
uvicorn main:app --reload --port 8000

# In another terminal, start frontend development server
cd ../frontend
npm run dev
```

The frontend will be available at http://localhost:5173 and the backend API at http://localhost:8000.

### Docker Development

```bash
# Build and start all services
docker-compose up --build

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📁 Project Structure

```
ui/
├── frontend/                   # React application
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API client services
│   │   ├── stores/            # Zustand state management
│   │   └── types/             # TypeScript type definitions
│   ├── public/                # Static assets
│   ├── package.json           # Node.js dependencies
│   └── Dockerfile            # Frontend container
├── backend/                   # FastAPI server
│   ├── main.py               # FastAPI application
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile           # Backend container
├── docker-compose.yml        # Multi-service orchestration
└── README.md                # This file
```

## 🎨 Design Inspiration

This interface draws inspiration from:

- **Modern web design principles** and user-centered design approaches
- **Glassmorphism** trend for depth and visual interest
- **Apple's Human Interface Guidelines** for clarity and usability
- **Material Design 3** for accessibility and responsive behavior
- **Contemporary UI frameworks** like Figma and Linear for clean, professional interfaces

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

## 🙏 Acknowledgments

- **React Team** for the amazing framework
- **Tailwind CSS** for utility-first styling
- **Framer Motion** for beautiful animations
- **Lucide** for clean, consistent icons
- **Recharts** for elegant data visualization
- **Modern web design community** for inspiration and best practices

---

Built with ❤️ using modern design principles.