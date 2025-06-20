#!/bin/bash
# Starts the UI stack with Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}🚀 Starting Anvyl UI Stack${NC}"

# Check if required files exist
if [[ ! -d "$PROJECT_ROOT/ui" ]]; then
    echo -e "${RED}❌ UI directory not found at $PROJECT_ROOT/ui${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

# Change to UI directory
cd "$PROJECT_ROOT/ui"

# Build and start the UI stack
echo -e "${BLUE}🏗️  Building and starting UI stack...${NC}"

# Build images first
echo -e "${YELLOW}📦 Building Docker images...${NC}"
docker-compose build

# Start services
echo -e "${YELLOW}🚀 Starting services...${NC}"
docker-compose up -d

# Wait a moment for services to start
sleep 5

# Check if services are running
echo -e "${YELLOW}🔍 Checking service status...${NC}"

FRONTEND_STATUS=$(docker-compose ps -q frontend 2>/dev/null || echo "")
BACKEND_STATUS=$(docker-compose ps -q backend 2>/dev/null || echo "")

if [[ -n "$FRONTEND_STATUS" ]] && [[ -n "$BACKEND_STATUS" ]]; then
    echo -e "${GREEN}✅ Anvyl UI stack started successfully!${NC}"
    echo ""
    echo -e "${BLUE}🌐 Access Points:${NC}"
    echo -e "   • Web UI:      ${GREEN}http://localhost:3000${NC}"
    echo -e "   • API Server:  ${GREEN}http://localhost:8000${NC}"
    echo ""
    echo -e "${YELLOW}📋 Useful Commands:${NC}"
    echo -e "   • View logs:   ${BLUE}docker-compose logs -f${NC}"
    echo -e "   • Stop stack:  ${BLUE}docker-compose down${NC}"
    echo -e "   • Restart:     ${BLUE}docker-compose restart${NC}"
else
    echo -e "${RED}❌ Failed to start UI stack${NC}"
    echo -e "${YELLOW}📋 Checking logs...${NC}"
    docker-compose logs
    exit 1
fi