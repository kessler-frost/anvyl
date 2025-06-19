#!/bin/bash

# Anvyl UI Startup Script
# Starts the gRPC server with Python and then the UI stack with Docker Compose

set -e

echo "🚀 Starting Anvyl Infrastructure"
echo "================================"

# Get the project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📁 Project root: $PROJECT_ROOT"

# Check if we're in the right directory
if [[ ! -f "$PROJECT_ROOT/anvyl/grpc_server.py" ]] || [[ ! -d "$PROJECT_ROOT/ui" ]]; then
    echo "❌ This doesn't appear to be the Anvyl project root."
    echo "   Please run this script from the Anvyl project directory."
    exit 1
fi

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Python virtual environment exists
if [[ ! -d "$PROJECT_ROOT/venv" ]]; then
    echo "❌ Python virtual environment not found."
    echo "   Please run the setup script first: ./scripts/dev_setup.sh"
    exit 1
fi

# Activate virtual environment
echo "🐍 Activating Python virtual environment..."
source "$PROJECT_ROOT/venv/bin/activate"

# Check if gRPC server is already running
if lsof -i :50051 >/dev/null 2>&1; then
    echo "⚠️  gRPC server is already running on port 50051"
else
    echo "🔧 Starting gRPC server..."
    cd "$PROJECT_ROOT"
    python -m anvyl.grpc_server &
    GRPC_PID=$!

    # Wait a moment for the server to start
    sleep 3

    # Check if the server started successfully
    if ! lsof -i :50051 >/dev/null 2>&1; then
        echo "❌ Failed to start gRPC server"
        exit 1
    fi

    echo "✅ gRPC server started (PID: $GRPC_PID)"
fi

# Start the UI stack
echo "🏗️  Starting UI stack..."
cd "$PROJECT_ROOT/ui"
docker-compose up -d

echo ""
echo "✅ Anvyl infrastructure started successfully!"
echo ""
echo "🌐 Access your Anvyl infrastructure:"
echo "   • Web UI:       http://localhost:3000"
echo "   • API Server:   http://localhost:8000"
echo "   • API Docs:     http://localhost:8000/docs"
echo "   • gRPC Server:  localhost:50051"
echo ""
echo "📋 Useful commands:"
echo "   • View logs:    docker-compose logs -f"
echo "   • Stop UI:      docker-compose down"
echo "   • Stop gRPC:    kill $GRPC_PID (if started by this script)"
echo ""