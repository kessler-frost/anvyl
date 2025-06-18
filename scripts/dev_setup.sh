#!/bin/bash

# Anvyl Development Setup Script
# Sets up the development environment for Anvyl infrastructure orchestrator

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
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is designed for macOS systems"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
if [[ "$PYTHON_VERSION" < "3.12" ]]; then
    print_error "Python 3.12+ is required. Current version: $PYTHON_VERSION"
    print_warning "Please install Python 3.12+ using Homebrew: brew install python@3.12"
    exit 1
fi

print_success "Python version check passed: $PYTHON_VERSION"

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    print_error "Homebrew is not installed. Please install it first:"
    echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# Install protobuf compiler if not present
if ! command -v protoc &> /dev/null; then
    print_status "Installing protobuf compiler..."
    brew install protobuf
    print_success "protobuf compiler installed"
else
    print_success "protobuf compiler already installed"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt
print_success "Python dependencies installed"

# Create generated directory for gRPC code
if [ ! -d "generated" ]; then
    print_status "Creating generated directory for gRPC code..."
    mkdir -p generated
fi

# Generate gRPC Python code from proto file
print_status "Generating gRPC Python code from proto file..."
if [ -f "protos/anvyl.proto" ]; then
    python -m grpc_tools.protoc \
        --python_out=generated \
        --grpc_python_out=generated \
        --proto_path=protos \
        protos/anvyl.proto

    # Create __init__.py in generated directory
    touch generated/__init__.py
    print_success "gRPC code generated successfully"
else
    print_error "Proto file not found at protos/anvyl.proto"
    exit 1
fi

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    print_warning "Docker is not installed. Please install Docker Desktop for Mac:"
    echo "  https://www.docker.com/products/docker-desktop/"
else
    if ! docker info &> /dev/null; then
        print_warning "Docker is installed but not running. Please start Docker Desktop."
    else
        print_success "Docker is installed and running"
    fi
fi

# Create database directory
if [ ! -d "database" ]; then
    print_status "Creating database directory..."
    mkdir -p database
fi

# Set up pre-commit hooks (optional)
if command -v pre-commit &> /dev/null; then
    print_status "Setting up pre-commit hooks..."
    pre-commit install
    print_success "Pre-commit hooks installed"
else
    print_warning "pre-commit not installed. Install with: pip install pre-commit"
fi

# Create .env file template if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file template..."
    cat > .env << EOF
# Anvyl Configuration
ANVYL_DATABASE_URL=sqlite:///anvyl.db
ANVYL_GRPC_PORT=50051
ANVYL_HOST=0.0.0.0

# Docker Configuration
DOCKER_HOST=unix:///var/run/docker.sock

# Development Configuration
DEBUG=true
LOG_LEVEL=INFO
EOF
    print_success ".env file created"
fi

print_success "🎉 Anvyl development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Start the gRPC server: python anvyl_grpc_server.py"
echo "3. Test the client: python -c \"from anvyl_sdk import create_client; client = create_client()\""
echo ""
echo "For more information, see the README.md file."