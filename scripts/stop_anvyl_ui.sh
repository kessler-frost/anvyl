#!/bin/bash

# Anvyl UI Stop Script
# Stops the UI stack and optionally the gRPC server

set -e

echo "🛑 Stopping Anvyl Infrastructure"
echo "================================"

# Get the project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📁 Project root: $PROJECT_ROOT"

# Stop the UI stack
echo "🏗️  Stopping UI stack..."
cd "$PROJECT_ROOT/ui"
docker-compose down

echo "✅ UI stack stopped"

# Check if user wants to stop gRPC server
read -p "Do you want to stop the gRPC server as well? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔧 Stopping gRPC server..."

    # Find and kill gRPC server processes
    PIDS=$(pgrep -f "python -m anvyl.grpc_server" || true)
    if [[ -n "$PIDS" ]]; then
        echo "Found gRPC server processes: $PIDS"
        kill $PIDS
        echo "✅ gRPC server stopped"
    else
        echo "⚠️  No gRPC server processes found"
    fi
else
    echo "ℹ️  gRPC server left running"
fi

echo ""
echo "✅ Anvyl infrastructure stopped successfully!"
echo ""