#!/bin/bash

# Anvyl Development Environment Setup Script
# This script sets up the complete development environment for Anvyl

set -e

echo "🔧 Setting up Anvyl development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "❌ This script is designed for macOS. Please set up manually."
    exit 1
fi

# Check if Homebrew is installed
if ! command -v brew >/dev/null 2>&1; then
    echo "❌ Homebrew is not installed. Please install it first: https://brew.sh"
    exit 1
fi

# Install protobuf compiler if not present
echo "📦 Installing/updating protobuf compiler..."
brew install protobuf

# Check for Python 3.12
if ! command -v python3.12 >/dev/null 2>&1; then
    echo "📦 Installing Python 3.12..."
    brew install python@3.12
fi

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
if [[ ! -d "venv" ]]; then
    python3.12 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Generate gRPC code from proto files
echo "🔧 Generating gRPC code..."
if [[ ! -d "generated" ]]; then
    mkdir generated
    touch generated/__init__.py
fi

python -m grpc_tools.protoc \
    --python_out=generated \
    --grpc_python_out=generated \
    --proto_path=protos \
    protos/anvyl.proto

echo "✅ gRPC code generated"

# Check Docker installation
echo "🐳 Checking Docker installation..."
if ! command -v docker >/dev/null 2>&1; then
    echo "⚠️ Docker is not installed. Please install Docker Desktop from: https://docker.com"
    echo "   Docker is required for container management."
else
    echo "✅ Docker is installed"
    
    # Check if Docker is running
    if docker info >/dev/null 2>&1; then
        echo "✅ Docker is running"
    else
        echo "⚠️ Docker is installed but not running. Please start Docker Desktop."
    fi
fi

# Create configuration directory
echo "📁 Creating configuration directories..."
mkdir -p logs
mkdir -p data

# Set up git hooks (if in a git repository)
if [[ -d ".git" ]]; then
    echo "🔗 Setting up git hooks..."
    # Future: Add pre-commit hooks for code formatting
fi

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Start the gRPC server: python anvyl_grpc_server.py"
echo "3. Or start the full UI stack: anvyl up"
echo ""
echo "📖 For more information, see README.md"