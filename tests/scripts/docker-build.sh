#!/bin/bash
# ==============================================================================
# Docker Build Script - Production Optimized
# Builds Docker images with caching and optimization
# ==============================================================================

set -e

echo "🐳 Building Docker Images for Production..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo -e "${YELLOW}⚠️  Warning: .env.production not found!${NC}"
    echo "Creating from template..."
    cp env.production.template .env.production
    echo -e "${RED}❌ Please edit .env.production with your actual values before deploying!${NC}"
    exit 1
fi

# Enable BuildKit for better caching
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build with caching
echo -e "${GREEN}📦 Building production image with BuildKit...${NC}"
docker-compose -f docker-compose.prod.yml build \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --parallel

# Tag the image
echo -e "${GREEN}🏷️  Tagging image...${NC}"
docker tag englishteacher_web:latest englishteacher_web:$(date +%Y%m%d-%H%M%S)

# Show image size
echo -e "${GREEN}📊 Image size:${NC}"
docker images englishteacher_web:latest --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

echo -e "${GREEN}✅ Build completed successfully!${NC}"
echo ""
echo "To start the application:"
echo "  docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.prod.yml logs -f"

