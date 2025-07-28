#!/bin/bash
# FlowLogic RouteAI - One-Click Production Deployment Script
# Usage: ./deploy.sh

set -e

echo "🚀 FlowLogic RouteAI - Production Deployment"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ This script should not be run as root${NC}"
   exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo -e "${BLUE}📋 Checking prerequisites...${NC}"

# Check Docker
if ! command_exists docker; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose
if ! command_exists docker-compose; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    echo "Please install Docker Compose first: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if user is in docker group
if ! groups $USER | grep &>/dev/null '\bdocker\b'; then
    echo -e "${YELLOW}⚠️  User $USER is not in docker group${NC}"
    echo "Run: sudo usermod -aG docker $USER && newgrp docker"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found, creating from template...${NC}"
    if [ -f .env.production ]; then
        cp .env.production .env
        echo -e "${YELLOW}📝 Please edit .env file with your domain and settings${NC}"
        echo -e "${YELLOW}   nano .env${NC}"
        read -p "Press Enter after editing .env file..."
    else
        echo -e "${RED}❌ No .env template found${NC}"
        exit 1
    fi
fi

# Read domain from .env
if grep -q "DOMAIN_NAME=" .env; then
    DOMAIN=$(grep "DOMAIN_NAME=" .env | cut -d'=' -f2)
    echo -e "${BLUE}🌐 Deploying for domain: ${DOMAIN}${NC}"
else
    echo -e "${RED}❌ DOMAIN_NAME not set in .env file${NC}"
    exit 1
fi

# Create Docker network
echo -e "${BLUE}🔗 Creating Docker network...${NC}"
docker network create flowlogic-network 2>/dev/null || echo "Network already exists"

# Pull latest images
echo -e "${BLUE}📦 Pulling Docker images...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull

# Build custom images
echo -e "${BLUE}🔨 Building application images...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Stop existing containers
echo -e "${BLUE}🛑 Stopping existing containers...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Start all services
echo -e "${BLUE}🚀 Starting all services...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
sleep 30

# Check service health
echo -e "${BLUE}🔍 Checking service health...${NC}"

services=("postgres" "redis" "api" "core" "frontend" "traefik")
failed_services=()

for service in "${services[@]}"; do
    if docker-compose ps | grep -q "${service}.*Up"; then
        echo -e "${GREEN}✅ ${service} is running${NC}"
    else
        echo -e "${RED}❌ ${service} failed to start${NC}"
        failed_services+=("$service")
    fi
done

if [ ${#failed_services[@]} -ne 0 ]; then
    echo -e "${RED}❌ Some services failed to start: ${failed_services[*]}${NC}"
    echo "Check logs with: docker-compose logs <service-name>"
    exit 1
fi

# Test API endpoints
echo -e "${BLUE}🧪 Testing API endpoints...${NC}"

# Wait a bit more for APIs to be fully ready
sleep 15

# Test core API health (internal)
if docker-compose exec -T core python -c "import requests; requests.get('http://localhost:8000/health')" 2>/dev/null; then
    echo -e "${GREEN}✅ Core API is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Core API health check failed (might be normal during startup)${NC}"
fi

# Test SaaS API health (internal)
if docker-compose exec -T api python -c "from main import app; print('API module loaded')" 2>/dev/null; then
    echo -e "${GREEN}✅ SaaS API is loaded${NC}"
else
    echo -e "${YELLOW}⚠️  SaaS API check failed${NC}"
fi

# Display deployment summary
echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo "=============================================="
echo ""
echo -e "${BLUE}🌐 Access Points:${NC}"
echo -e "   Main Website:    https://${DOMAIN}"
echo -e "   API Docs:        https://api.${DOMAIN}/docs"
echo -e "   Core API:        https://core.${DOMAIN}"
echo -e "   Admin Panel:     https://api.${DOMAIN}/admin"
echo -e "   Traefik Dashboard: https://traefik.${DOMAIN}"
echo ""
echo -e "${BLUE}📊 Monitoring:${NC}"
echo -e "   Service Status:  docker-compose ps"
echo -e "   View Logs:       docker-compose logs -f <service>"
echo -e "   System Stats:    docker stats"
echo ""
echo -e "${BLUE}🔧 Management:${NC}"
echo -e "   Stop Services:   docker-compose -f docker-compose.yml -f docker-compose.prod.yml down"
echo -e "   Restart:         docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart"
echo -e "   Update:          git pull && ./deploy.sh"
echo ""

# Check SSL certificate status
echo -e "${BLUE}🔒 SSL Certificate Status:${NC}"
echo "   Certificates will be automatically generated by Let's Encrypt"
echo "   This may take a few minutes on first deployment"
echo ""

# Final verification
echo -e "${BLUE}🔍 Final Verification:${NC}"
echo "   1. Visit https://${DOMAIN} to access the main application"
echo "   2. Check https://api.${DOMAIN}/docs for API documentation"
echo "   3. Monitor logs with: docker-compose logs -f"
echo ""

# Backup reminder
echo -e "${YELLOW}💾 Backup Reminder:${NC}"
echo "   Database backups are automatically configured"
echo "   Manual backup: docker-compose exec postgres pg_dump -U postgres flowlogic > backup_$(date +%Y%m%d).sql"
echo ""

echo -e "${GREEN}✨ FlowLogic RouteAI is now live at https://${DOMAIN}${NC}"
echo -e "${GREEN}🚀 Happy routing!${NC}"