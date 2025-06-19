#!/bin/bash
"""
Anvyl CLI Demo Script
This script demonstrates the key features of the Anvyl CLI
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔨 Anvyl CLI Demo${NC}"
echo "=================="
echo ""

# Check if anvyl command is available
if ! command -v anvyl &> /dev/null; then
    echo -e "${RED}Error: 'anvyl' command not found. Please install the CLI first:${NC}"
    echo "  ./scripts/install_cli.sh"
    exit 1
fi

echo -e "${GREEN}✓ Anvyl CLI is installed${NC}"
echo ""

echo -e "${CYAN}Demo 1: Show CLI version and help${NC}"
echo "=================================="
anvyl version
echo ""
echo -e "${YELLOW}Available commands:${NC}"
anvyl --help | head -20
echo ""

echo -e "${CYAN}Demo 2: Check system status${NC}"
echo "============================"
echo -e "${YELLOW}Note: This will fail if the gRPC server is not running${NC}"
echo -e "${YELLOW}Start it with: python anvyl_grpc_server.py${NC}"
echo ""

# Try to connect and show status (this might fail if server is not running)
if anvyl status 2>/dev/null; then
    echo -e "${GREEN}✓ Successfully connected to Anvyl server${NC}"
else
    echo -e "${YELLOW}⚠ Could not connect to Anvyl server${NC}"
    echo -e "${YELLOW}  This is expected if the server is not running${NC}"
    echo -e "${YELLOW}  Start it with: python anvyl_grpc_server.py${NC}"
fi
echo ""

echo -e "${CYAN}Demo 3: Show host management commands${NC}"
echo "====================================="
echo -e "${YELLOW}List hosts (will show empty if no server or no hosts):${NC}"
if anvyl host list 2>/dev/null; then
    echo -e "${GREEN}✓ Host list command successful${NC}"
else
    echo -e "${YELLOW}⚠ Could not list hosts (server not running)${NC}"
fi
echo ""

echo -e "${YELLOW}Host management help:${NC}"
anvyl host --help
echo ""

echo -e "${CYAN}Demo 4: Show container management commands${NC}"
echo "=========================================="
echo -e "${YELLOW}Container management help:${NC}"
anvyl container --help
echo ""

echo -e "${YELLOW}Container creation example (would create if server running):${NC}"
echo "anvyl container create \"demo-web\" \"nginx:alpine\" --port \"8080:80\" --label \"demo=true\""
echo ""

echo -e "${CYAN}Demo 5: Show agent management commands${NC}"
echo "======================================"
echo -e "${YELLOW}Agent management help:${NC}"
anvyl agent --help
echo ""

echo -e "${CYAN}Demo 6: JSON output example${NC}"
echo "========================="
echo -e "${YELLOW}All commands support JSON output for scripting:${NC}"
echo "anvyl host list --output json"
echo "anvyl container list --output json"
echo "anvyl agent list --output json"
echo ""

echo -e "${CYAN}Demo 7: Remote server connection example${NC}"
echo "========================================"
echo -e "${YELLOW}Connect to remote Anvyl server:${NC}"
echo "anvyl --host 192.168.1.100 --port 50051 status"
echo "anvyl --host 192.168.1.100 host list"
echo ""

echo -e "${GREEN}🎉 Demo complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Start the gRPC server: ${YELLOW}python anvyl_grpc_server.py${NC}"
echo "2. Try the commands shown above"
echo "3. Read the full documentation: ${YELLOW}docs/cli_usage.md${NC}"
echo "4. Add your first host: ${YELLOW}anvyl host add \"my-mac\" \"192.168.1.100\"${NC}"
echo "5. Create your first container: ${YELLOW}anvyl container create \"test\" \"nginx:alpine\"${NC}"
echo ""
echo -e "${YELLOW}For help with any command, use --help:${NC}"
echo "  anvyl --help"
echo "  anvyl host --help"
echo "  anvyl container create --help"