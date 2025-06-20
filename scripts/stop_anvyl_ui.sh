#!/bin/bash
# Stops the UI stack

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}🛑 Stopping Anvyl UI Stack${NC}"

# Check if UI directory exists
if [[ ! -d "$PROJECT_ROOT/ui" ]]; then
    echo -e "${RED}❌ UI directory not found at $PROJECT_ROOT/ui${NC}"
    exit 1
fi

# Change to UI directory
cd "$PROJECT_ROOT/ui"

# Stop the UI stack
echo -e "${YELLOW}🛑 Stopping UI services...${NC}"
docker-compose down

echo -e "${GREEN}✅ Anvyl UI stack stopped successfully!${NC}"