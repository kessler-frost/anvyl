#!/bin/bash

# Anvyl Development Setup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Anvyl Development Setup${NC}"
echo "================================"

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo -e "${BLUE}📁 Project root: $PROJECT_ROOT${NC}"

# Check if we're in the right directory
if [[ ! -f "$PROJECT_ROOT/pyproject.toml" ]]; then
    echo -e "${RED}❌ This doesn't appear to be the Anvyl project root.${NC}"
    echo -e "${RED}   Please run this script from the Anvyl project directory.${NC}"
    exit 1
fi

# Check Python version
echo -e "${YELLOW}🐍 Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
required_version="3.12"

if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
    echo -e "${RED}❌ Python $required_version or higher is required. Found: $python_version${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $python_version is compatible${NC}"

# Check if Docker is available
echo -e "${YELLOW}🐳 Checking Docker...${NC}"
if command -v docker &> /dev/null; then
    if docker info > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker is available and running${NC}"
    else
        echo -e "${YELLOW}⚠️  Docker is installed but not running${NC}"
        echo -e "${YELLOW}   Please start Docker and run this script again${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Docker not found${NC}"
    echo -e "${YELLOW}   Please install Docker to use containerized features${NC}"
fi

# Create virtual environment
echo -e "${YELLOW}🐍 Creating Python virtual environment...${NC}"
if [[ -d "$PROJECT_ROOT/venv" ]]; then
    echo -e "${YELLOW}⚠️  Virtual environment already exists. Removing...${NC}"
    rm -rf "$PROJECT_ROOT/venv"
fi

python3 -m venv "$PROJECT_ROOT/venv"
echo -e "${GREEN}✅ Virtual environment created${NC}"

# Activate virtual environment
echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source "$PROJECT_ROOT/venv/bin/activate"

# Upgrade pip
echo -e "${YELLOW}📦 Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
pip install -e .

echo -e "${GREEN}✅ Dependencies installed successfully${NC}"

# Create necessary directories
echo -e "${YELLOW}📁 Creating necessary directories...${NC}"
mkdir -p "$PROJECT_ROOT/anvyl/agents"
mkdir -p ~/.anvyl/agents

echo -e "${GREEN}✅ Directories created${NC}"

# Install CLI
echo -e "${YELLOW}🔧 Installing CLI...${NC}"
pip install -e .

echo -e "${GREEN}✅ CLI installed successfully${NC}"

# Test installation
echo -e "${YELLOW}🧪 Testing installation...${NC}"
if command -v anvyl &> /dev/null; then
    echo -e "${GREEN}✅ CLI is available${NC}"
    anvyl --version
else
    echo -e "${RED}❌ CLI installation failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Anvyl development setup completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo -e "1. Start the UI stack: ${YELLOW}./scripts/start_anvyl_ui.sh${NC}"
echo -e "2. Create an AI agent: ${YELLOW}anvyl agent create my-agent --provider lmstudio --auto-start${NC}"
echo -e "3. Execute instructions: ${YELLOW}anvyl agent act my-agent \"Show me all hosts\"${NC}"
echo ""
echo -e "${BLUE}📚 Useful Commands:${NC}"
echo -e "• ${YELLOW}anvyl --help${NC} - Show CLI help"
echo -e "• ${YELLOW}anvyl agent --help${NC} - Show agent commands"
echo -e "• ${YELLOW}anvyl status${NC} - Show system status"
echo ""
echo -e "${BLUE}🔧 Development:${NC}"
echo -e "• Activate venv: ${YELLOW}source venv/bin/activate${NC}"
echo -e "• Run tests: ${YELLOW}python -m pytest${NC}"
echo -e "• Stop UI: ${YELLOW}./scripts/stop_anvyl_ui.sh${NC}"