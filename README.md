# Anvyl

<p align="center">
  <b>The blacksmith for your self‑hosted Apple infrastructure.</b><br>
  <img alt="License" src="https://img.shields.io/badge/license-Apache%202.0-blue">
  <img alt="Python" src="https://img.shields.io/badge/python-3.12-blue">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white">
  <img alt="React" src="https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB">
</p>

**Anvyl** is a modern container orchestration platform designed for Apple Silicon-first environments. Built for small-scale, self-hosted setups, it offers a clean web interface, RESTful API, and seamless multi-machine coordination. Simple to deploy, powerful when extended.

---

## ✨ Features

- 🌐 Modern React-based web dashboard
- 🔌 RESTful FastAPI backend with automatic OpenAPI docs
- 💾 SQLite database with SQLModel ORM
- 🐳 Docker container management
- 🔐 Secure host provisioning with pyinfra
- 🧱 Modular architecture for future agent support
- 📱 Responsive design with Tailwind CSS

---

## 🛠 Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **SQLModel** - SQL databases in Python, designed for simplicity and compatibility
- **pyinfra** - Infrastructure automation tool
- **SQLite** - Lightweight, serverless database

### Frontend
- **React 18** - Modern UI library with TypeScript
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API communication

### Infrastructure
- **Docker** - Containerization platform
- **Docker Compose** - Multi-container orchestration

---

## 🚀 Quickstart

### Prerequisites
- Python 3.12+
- Node.js 18+
- Docker & Docker Compose

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd anvyl

# Backend setup
pip install -r requirements.txt

# Frontend setup
cd src/ui
npm install

# Start development servers
# Terminal 1 - Backend
cd ../../
uvicorn src.anvyl.main:app --reload --port 8000

# Terminal 2 - Frontend
cd src/ui
npm run dev
```

### Production Deployment

```bash
# Using Docker Compose
docker-compose up --build

# Access the application
# Backend API: http://localhost:8000
# Frontend UI: http://localhost:4173
# API Docs: http://localhost:8000/docs
```

---

## 📁 Project Structure

```
anvyl/
├── src/
│   ├── anvyl/            # FastAPI backend
│   │   ├── api/          # API routes and endpoints
│   │   ├── db/           # Database models and session
│   │   ├── models/       # Data models
│   │   └── main.py       # FastAPI application entry point
│   └── ui/               # React frontend
│       ├── src/          # React components and logic
│       ├── public/       # Static assets
│       └── package.json  # Node.js dependencies
├── docker-compose.yml    # Multi-container orchestration
├── Dockerfile.api        # Backend container configuration
└── requirements.txt      # Python dependencies
```

---

## 🔧 API Endpoints

The FastAPI backend provides automatic OpenAPI documentation at `/docs`. Key endpoints include:

- `GET /api/hosts` - List managed hosts
- `POST /api/hosts` - Add new host
- `GET /api/hosts/{host_id}` - Get host details
- `PUT /api/hosts/{host_id}` - Update host configuration
- `DELETE /api/hosts/{host_id}` - Remove host

---

## 📦 Roadmap

- [x] FastAPI backend with SQLite database
- [x] React frontend with Tailwind CSS
- [x] Docker containerization
- [x] Host management API
- [ ] Container lifecycle management
- [ ] Real-time container monitoring
- [ ] Multi-machine coordination
- [ ] Apple Container runtime support (macOS 16+)
- [ ] Advanced provisioning with pyinfra
- [ ] Container logs, exec, and metrics
- [ ] Authentication and authorization
- [ ] Plugin system for custom integrations

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Inspired by the need for simple, powerful container orchestration on Apple Silicon
- Built with modern web technologies for developer productivity
- Designed for self-hosted infrastructure enthusiasts
