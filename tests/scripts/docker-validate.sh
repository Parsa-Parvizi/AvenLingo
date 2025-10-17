#!/bin/bash
# ==============================================================================
# Docker Configuration Validation Script
# Validates all Docker-related files before deployment
# ==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

echo -e "${BLUE}🔍 Docker Configuration Validation${NC}"
echo "===================================="
echo ""

# Function to check file existence
check_file() {
    local file=$1
    local required=$2
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅${NC} $file exists"
        return 0
    else
        if [ "$required" = "required" ]; then
            echo -e "${RED}❌${NC} $file is missing (REQUIRED)"
            ((ERRORS++))
        else
            echo -e "${YELLOW}⚠️${NC}  $file is missing (optional)"
            ((WARNINGS++))
        fi
        return 1
    fi
}

# Function to validate Docker Compose file
validate_compose() {
    local file=$1
    echo ""
    echo -e "${BLUE}📋 Validating $file...${NC}"
    
    if docker-compose -f "$file" config > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC} $file syntax is valid"
    else
        echo -e "${RED}❌${NC} $file has syntax errors:"
        docker-compose -f "$file" config 2>&1 | head -n 10
        ((ERRORS++))
    fi
}

# Function to check Dockerfile syntax
validate_dockerfile() {
    local file=$1
    echo ""
    echo -e "${BLUE}🐳 Validating $file...${NC}"
    
    # Check for common issues
    if grep -q "^FROM" "$file"; then
        echo -e "${GREEN}✅${NC} Has FROM instruction"
    else
        echo -e "${RED}❌${NC} Missing FROM instruction"
        ((ERRORS++))
    fi
    
    if grep -q "^COPY\|^ADD" "$file"; then
        echo -e "${GREEN}✅${NC} Has COPY/ADD instruction"
    else
        echo -e "${YELLOW}⚠️${NC}  No COPY/ADD instruction found"
        ((WARNINGS++))
    fi
    
    # Check for best practices
    if grep -q "PYTHONUNBUFFERED" "$file"; then
        echo -e "${GREEN}✅${NC} Sets PYTHONUNBUFFERED"
    else
        echo -e "${YELLOW}⚠️${NC}  PYTHONUNBUFFERED not set"
        ((WARNINGS++))
    fi
    
    if grep -q "HEALTHCHECK" "$file"; then
        echo -e "${GREEN}✅${NC} Has HEALTHCHECK"
    else
        echo -e "${YELLOW}⚠️${NC}  No HEALTHCHECK defined"
        ((WARNINGS++))
    fi
}

# Check Docker installation
echo -e "${BLUE}🔧 Checking Docker installation...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅${NC} Docker is installed: $(docker --version)"
else
    echo -e "${RED}❌${NC} Docker is not installed"
    ((ERRORS++))
fi

if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✅${NC} Docker Compose is installed: $(docker-compose --version)"
else
    echo -e "${RED}❌${NC} Docker Compose is not installed"
    ((ERRORS++))
fi

# Check required files
echo ""
echo -e "${BLUE}📁 Checking required files...${NC}"
check_file "Dockerfile" "required"
check_file "docker-compose.yml" "required"
check_file "docker-compose.prod.yml" "required"
check_file ".dockerignore" "required"
check_file "requirements.txt" "required"
check_file "setup/entrypoint.sh" "required"

# Check optional files
echo ""
echo -e "${BLUE}📁 Checking optional files...${NC}"
check_file "docker.env" "optional"
check_file ".env.production" "optional"
check_file "env.production.template" "optional"
check_file "env.development.template" "optional"

# Validate Docker files
if [ -f "Dockerfile" ]; then
    validate_dockerfile "Dockerfile"
fi

if [ -f "docker-compose.yml" ]; then
    validate_compose "docker-compose.yml"
fi

if [ -f "docker-compose.prod.yml" ]; then
    validate_compose "docker-compose.prod.yml"
fi

# Check entrypoint.sh permissions
echo ""
echo -e "${BLUE}🔐 Checking file permissions...${NC}"
if [ -f "setup/entrypoint.sh" ]; then
    if [ -x "setup/entrypoint.sh" ]; then
        echo -e "${GREEN}✅${NC} entrypoint.sh is executable"
    else
        echo -e "${YELLOW}⚠️${NC}  entrypoint.sh is not executable (fixing...)"
        chmod +x setup/entrypoint.sh
        ((WARNINGS++))
    fi
fi

# Check .dockerignore content
echo ""
echo -e "${BLUE}📝 Checking .dockerignore...${NC}"
if [ -f ".dockerignore" ]; then
    critical_entries=("venv/" "__pycache__/" ".git/" "*.pyc" "*.log")
    for entry in "${critical_entries[@]}"; do
        if grep -q "$entry" ".dockerignore"; then
            echo -e "${GREEN}✅${NC} Excludes $entry"
        else
            echo -e "${YELLOW}⚠️${NC}  Should exclude $entry"
            ((WARNINGS++))
        fi
    done
fi

# Check requirements.txt
echo ""
echo -e "${BLUE}📦 Checking requirements.txt...${NC}"
if [ -f "requirements.txt" ]; then
    # Check for Django
    if grep -q "^Django" "requirements.txt"; then
        echo -e "${GREEN}✅${NC} Contains Django"
    else
        echo -e "${RED}❌${NC} Missing Django"
        ((ERRORS++))
    fi
    
    # Check for psycopg2
    if grep -q "psycopg2" "requirements.txt"; then
        echo -e "${GREEN}✅${NC} Contains PostgreSQL driver"
    else
        echo -e "${YELLOW}⚠️${NC}  No PostgreSQL driver found"
        ((WARNINGS++))
    fi
    
    # Check for gunicorn
    if grep -q "gunicorn" "requirements.txt"; then
        echo -e "${GREEN}✅${NC} Contains Gunicorn"
    else
        echo -e "${YELLOW}⚠️${NC}  No production server (gunicorn) found"
        ((WARNINGS++))
    fi
    
    # Count total dependencies
    dep_count=$(grep -c "^[^#]" "requirements.txt" || true)
    echo -e "${BLUE}ℹ️${NC}  Total dependencies: $dep_count"
    if [ "$dep_count" -lt 50 ]; then
        echo -e "${GREEN}✅${NC} Dependency count is optimal (< 50)"
    else
        echo -e "${YELLOW}⚠️${NC}  Many dependencies ($dep_count). Consider optimization."
        ((WARNINGS++))
    fi
fi

# Security checks
echo ""
echo -e "${BLUE}🔒 Security checks...${NC}"

if [ -f "docker.env" ]; then
    if grep -q "SECRET_KEY.*change" "docker.env"; then
        echo -e "${YELLOW}⚠️${NC}  docker.env contains default SECRET_KEY"
        ((WARNINGS++))
    fi
    
    if grep -q "PASSWORD.*change" "docker.env"; then
        echo -e "${YELLOW}⚠️${NC}  docker.env contains default PASSWORD"
        ((WARNINGS++))
    fi
fi

if [ -f ".env.production" ]; then
    if grep -q "DEBUG.*True" ".env.production"; then
        echo -e "${RED}❌${NC} Production env has DEBUG=True"
        ((ERRORS++))
    else
        echo -e "${GREEN}✅${NC} Production DEBUG is False"
    fi
fi

# Check for .env in .gitignore
if [ -f ".gitignore" ]; then
    if grep -q "\.env" ".gitignore"; then
        echo -e "${GREEN}✅${NC} .env files are in .gitignore"
    else
        echo -e "${RED}❌${NC} .env files are NOT in .gitignore (security risk!)"
        ((ERRORS++))
    fi
fi

# Test Docker build (optional)
echo ""
echo -e "${BLUE}🔨 Testing Docker build (dry-run)...${NC}"
if docker-compose config > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} Docker Compose configuration is valid"
else
    echo -e "${RED}❌${NC} Docker Compose configuration has errors"
    ((ERRORS++))
fi

# Summary
echo ""
echo "===================================="
echo -e "${BLUE}📊 Validation Summary${NC}"
echo "===================================="

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ Errors: 0${NC}"
else
    echo -e "${RED}❌ Errors: $ERRORS${NC}"
fi

if [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ Warnings: 0${NC}"
else
    echo -e "${YELLOW}⚠️  Warnings: $WARNINGS${NC}"
fi

echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All critical checks passed!${NC}"
    echo -e "${GREEN}   Ready for deployment.${NC}"
    exit 0
else
    echo -e "${RED}❌ Please fix the errors before deploying.${NC}"
    exit 1
fi

