#!/bin/bash
# ==============================================================================
# Docker Development Script
# Quick start for local development
# ==============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Starting Development Environment...${NC}"

# Check if docker.env exists
if [ ! -f docker.env ]; then
    echo -e "${YELLOW}⚠️  docker.env not found, creating from template...${NC}"
    cp env.development.template docker.env
fi

# Enable BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Start services
echo -e "${GREEN}📦 Building and starting services...${NC}"
docker-compose up --build -d

# Show logs
echo -e "${GREEN}📝 Showing logs (Ctrl+C to exit)...${NC}"
docker-compose logs -f

