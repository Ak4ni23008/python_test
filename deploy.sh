#!/bin/bash

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   CloudTrade Oracle Deployment v1.0   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo -e "${YELLOW}Install Docker: https://docs.docker.com/engine/install/ubuntu/${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not installed${NC}"
    echo -e "${YELLOW}Install Docker Compose: https://docs.docker.com/compose/install/${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose found${NC}"
echo ""

# Load environment variables or create .env
if [ ! -f .env.prod ]; then
    echo -e "${YELLOW}Creating .env.prod file...${NC}"
    cat > .env.prod << EOF
# Database
DB_PASSWORD=\$(openssl rand -base64 32)

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# Frontend
NEXT_PUBLIC_API_URL=http://localhost

# Environment
ENVIRONMENT=production
CORS_ORIGINS=http://localhost,https://your-domain.com

EOF
    echo -e "${YELLOW}⚠ Please edit .env.prod with your API keys!${NC}"
    echo -e "${YELLOW}Waiting 5 seconds before proceeding...${NC}"
    sleep 5
fi

# Load .env
set -a
source .env.prod
set +a

echo -e "${BLUE}Building Docker images...${NC}"
docker-compose -f docker-compose.yml --env-file .env.prod build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Build successful${NC}"
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Starting services...${NC}"
docker-compose -f docker-compose.yml --env-file .env.prod up -d

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Services started${NC}"
else
    echo -e "${RED}✗ Failed to start services${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Waiting for services to be healthy...${NC}"
sleep 10

# Check service health
echo ""
echo -e "${BLUE}Service Status:${NC}"
echo ""

# Backend health
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓ Backend (FastAPI)${NC}"
else
    echo -e "${RED}✗ Backend (FastAPI)${NC}"
fi

# Frontend health
if curl -s http://localhost:3000 > /dev/null; then
    echo -e "${GREEN}✓ Frontend (Next.js)${NC}"
else
    echo -e "${RED}✗ Frontend (Next.js)${NC}"
fi

# Database health
if docker exec cloudtrade-db pg_isready -U cloudtrade > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database (PostgreSQL)${NC}"
else
    echo -e "${RED}✗ Database (PostgreSQL)${NC}"
fi

# Worker health
if docker ps | grep cloudtrade-worker > /dev/null; then
    echo -e "${GREEN}✓ Worker (Live Trading)${NC}"
else
    echo -e "${RED}✗ Worker (Live Trading)${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""
echo -e "📱 Frontend: ${YELLOW}http://localhost:3000${NC}"
echo -e "🔧 Backend:  ${YELLOW}http://localhost:8000${NC}"
echo -e "📊 API Docs: ${YELLOW}http://localhost:8000/docs${NC}"
echo ""
echo -e "${BLUE}Useful Commands:${NC}"
echo "  View logs:       docker-compose logs -f"
echo "  Stop services:   docker-compose down"
echo "  Restart:         docker-compose restart"
echo "  Update code:     git pull && docker-compose up -d --build"
echo ""
