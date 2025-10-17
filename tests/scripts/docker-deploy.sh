#!/bin/bash
# ==============================================================================
# Docker Deploy Script - Production Deployment
# Deploys the application with zero-downtime strategy
# ==============================================================================

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Deploying English Teacher Academy - Production${NC}"
echo "=================================================="

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo -e "${RED}❌ Error: .env.production not found!${NC}"
    echo "Please create it from env.production.template"
    exit 1
fi

# Load environment variables
export $(cat .env.production | grep -v '^#' | xargs)

# Validate required variables
REQUIRED_VARS=("DJANGO_SECRET_KEY" "POSTGRES_PASSWORD" "DJANGO_ALLOWED_HOSTS")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}❌ Error: $var is not set in .env.production${NC}"
        exit 1
    fi
done

# Check if secret key is still default
if [[ "$DJANGO_SECRET_KEY" == *"change-this"* ]]; then
    echo -e "${RED}❌ Error: Please change DJANGO_SECRET_KEY in .env.production${NC}"
    exit 1
fi

# Enable BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build images
echo -e "${GREEN}📦 Building Docker images...${NC}"
docker-compose -f docker-compose.prod.yml build --parallel

# Create backup of database (if exists)
if docker ps -a | grep -q englishteacher_db_prod; then
    echo -e "${YELLOW}💾 Creating database backup...${NC}"
    mkdir -p backups
    docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U $POSTGRES_USER $POSTGRES_DB > "backups/backup_$(date +%Y%m%d_%H%M%S).sql" || true
fi

# Pull database image
echo -e "${GREEN}📥 Pulling PostgreSQL image...${NC}"
docker-compose -f docker-compose.prod.yml pull db

# Start database first
echo -e "${GREEN}🗄️  Starting database...${NC}"
docker-compose -f docker-compose.prod.yml up -d db

# Wait for database to be healthy
echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"
timeout 60 bash -c 'until docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U $POSTGRES_USER; do sleep 2; done'

# Run migrations
echo -e "${GREEN}🔄 Running database migrations...${NC}"
docker-compose -f docker-compose.prod.yml run --rm web python manage.py migrate --noinput

# Collect static files
echo -e "${GREEN}📦 Collecting static files...${NC}"
docker-compose -f docker-compose.prod.yml run --rm web python manage.py collectstatic --noinput --clear

# Start all services
echo -e "${GREEN}🚀 Starting all services...${NC}"
docker-compose -f docker-compose.prod.yml up -d

# Wait for web service to be healthy
echo -e "${YELLOW}⏳ Waiting for web service to be ready...${NC}"
sleep 10

# Check service health
echo -e "${GREEN}🏥 Checking service health...${NC}"
docker-compose -f docker-compose.prod.yml ps

# Show logs
echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.prod.yml ps
echo ""
echo "📝 To view logs:"
echo "  docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "🔍 To check application:"
echo "  curl http://localhost"
echo ""
echo "🛑 To stop services:"
echo "  docker-compose -f docker-compose.prod.yml down"

