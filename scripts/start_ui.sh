#!/bin/bash

# Anvyl UI Quick Start Script
# This script helps users quickly start the Anvyl infrastructure with UI

set -e

echo "🚀 Anvyl UI Quick Start"
echo "======================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose >/dev/null 2>&1; then
    echo "❌ docker-compose is not installed. Please install it and try again."
    exit 1
fi

# Get the project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📁 Project root: $PROJECT_ROOT"

# Check if we're in the right directory
if [[ ! -f "$PROJECT_ROOT/anvyl_grpc_server.py" ]] || [[ ! -d "$PROJECT_ROOT/ui" ]]; then
    echo "❌ This doesn't appear to be the Anvyl project root."
    echo "   Please run this script from the Anvyl project directory."
    exit 1
fi

# Install Python dependencies if needed
if [[ ! -d "$PROJECT_ROOT/venv" ]]; then
    echo "🔧 Setting up Python virtual environment..."
    cd "$PROJECT_ROOT"
    python3.12 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "✅ Python virtual environment exists"
fi

# Start the infrastructure
echo ""
echo "🏗️ Starting Anvyl infrastructure..."
cd "$PROJECT_ROOT"

# Use the CLI if available, otherwise use docker-compose directly
if [[ -f "anvyl_cli.py" ]]; then
    echo "Using Anvyl CLI..."
    source venv/bin/activate
    python anvyl_cli.py up --build
else
    echo "Using docker-compose directly..."
    cd ui
    docker-compose up -d --build
fi

echo ""
echo "✅ Anvyl UI started successfully!"
echo ""
echo "🌐 Access your Anvyl infrastructure:"
echo "   • Web UI:       http://localhost:3000"
echo "   • API Server:   http://localhost:8000"
echo "   • API Docs:     http://localhost:8000/docs"
echo "   • gRPC Server:  localhost:50051"
echo ""
echo "📋 Useful commands:"
echo "   • View logs:    anvyl logs"
echo "   • Check status: anvyl ps"
echo "   • Stop stack:   anvyl down"
echo ""
echo "💡 The beautiful Komodo-inspired UI is now running!"