#!/bin/bash
"""
Anvyl CLI Installation Script
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔨 Anvyl CLI Installation Script${NC}"
echo "=================================="

# Check if Python 3.12+ is available
echo -e "${YELLOW}Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
required_version="3.12"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)" 2>/dev/null; then
    echo -e "${RED}Error: Python 3.12+ is required. Current version: ${python_version}${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python ${python_version} detected${NC}"

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo -e "${GREEN}✓ Virtual environment detected: $VIRTUAL_ENV${NC}"
else
    echo -e "${YELLOW}Warning: No virtual environment detected. Consider using one.${NC}"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Exiting. Please activate a virtual environment and try again.${NC}"
        exit 1
    fi
fi

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Install Anvyl CLI in development mode
echo -e "${YELLOW}Installing Anvyl CLI...${NC}"
pip install -e .

# Verify installation
echo -e "${YELLOW}Verifying installation...${NC}"
if command -v anvyl &> /dev/null; then
    echo -e "${GREEN}✓ Anvyl CLI installed successfully!${NC}"
    anvyl --help
else
    echo -e "${RED}✗ Installation failed. The 'anvyl' command is not available.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Installation complete!${NC}"
echo -e "${BLUE}Usage examples:${NC}"
echo "  anvyl status                    # Show system status"
echo "  anvyl host list                 # List all hosts"
echo "  anvyl container list            # List all containers"
echo "  anvyl container create web nginx:alpine --port 8080:80"
echo "  anvyl --help                    # Show full help"
echo "  anvyl agent up                    # Start the AI agent on this host"
echo "  anvyl agent down                  # Stop the AI agent on this host"
echo "  anvyl agent query \"List all containers on this host\""
echo "  anvyl agent hosts                 # List agent hosts"
echo "  anvyl agent add-host <host-id> <host-ip>"
echo ""
echo -e "${YELLOW}Note: Make sure the Anvyl gRPC server is running before using the CLI.${NC}"
echo "Start it with: python anvyl_grpc_server.py"