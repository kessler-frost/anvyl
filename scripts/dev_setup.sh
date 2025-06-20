#!/bin/bash

# Anvyl Development Setup Script
# This script sets up the development environment for Anvyl

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Anvyl Development Setup${NC}"
echo "=============================="
echo ""

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo -e "${CYAN}Project root: ${PROJECT_ROOT}${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "${PROJECT_ROOT}/pyproject.toml" ]; then
    echo -e "${RED}Error: pyproject.toml not found. Please run this script from the Anvyl project root.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found Anvyl project${NC}"
echo ""

# Check Python version
echo -e "${CYAN}Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${YELLOW}Python version: ${PYTHON_VERSION}${NC}"

# Check if Python 3.12+ is available
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    echo -e "${GREEN}✓ Python 3.12+ found${NC}"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo -e "${GREEN}✓ Python 3.11 found${NC}"
elif command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
    echo -e "${GREEN}✓ Python 3.10 found${NC}"
else
    echo -e "${YELLOW}⚠ Python 3.10+ recommended, but using available Python${NC}"
    PYTHON_CMD="python3"
fi
echo ""

# Check Docker
echo -e "${CYAN}Checking Docker...${NC}"
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓ Docker found: ${DOCKER_VERSION}${NC}"

    # Check if Docker is running
    if docker info &> /dev/null; then
        echo -e "${GREEN}✓ Docker is running${NC}"
    else
        echo -e "${YELLOW}⚠ Docker is installed but not running${NC}"
        echo -e "${YELLOW}  Please start Docker Desktop and try again${NC}"
    fi
else
    echo -e "${RED}✗ Docker not found${NC}"
    echo -e "${YELLOW}  Please install Docker Desktop: https://www.docker.com/products/docker-desktop${NC}"
    exit 1
fi
echo ""

# Create virtual environment
echo -e "${CYAN}Setting up virtual environment...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo -e "${CYAN}Upgrading pip...${NC}"
pip install --upgrade pip
echo -e "${GREEN}✓ Pip upgraded${NC}"
echo ""

# Install development dependencies
echo -e "${CYAN}Installing development dependencies...${NC}"
pip install -e ".[dev]"
echo -e "${GREEN}✓ Development dependencies installed${NC}"
echo ""

# Create necessary directories
echo -e "${CYAN}Creating necessary directories...${NC}"
mkdir -p ~/.anvyl
mkdir -p ~/.anvyl/logs
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Run tests to verify installation
echo -e "${CYAN}Running tests to verify installation...${NC}"
if python -m pytest tests/ -v; then
    echo -e "${GREEN}✓ Tests passed${NC}"
else
    echo -e "${YELLOW}⚠ Some tests failed (this might be expected in development)${NC}"
fi
echo ""

# Show next steps
echo -e "${GREEN}🎉 Development environment setup complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Activate the virtual environment: ${YELLOW}source venv/bin/activate${NC}"
echo "2. Start the infrastructure: ${YELLOW}anvyl up${NC}"
echo "3. Access the web UI: ${YELLOW}http://localhost:3000${NC}"
echo "4. Run the CLI demo: ${YELLOW}./scripts/demo_cli.sh${NC}"
echo "5. Run tests: ${YELLOW}python -m pytest${NC}"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "  anvyl --help                    # Show CLI help"
echo "  anvyl status                    # Check system status"
echo "  anvyl host list                 # List hosts"
echo "  anvyl container list            # List containers"
echo "  python -m pytest                # Run tests"
echo "  python -m pytest -v             # Run tests with verbose output"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"