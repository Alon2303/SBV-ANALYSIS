#!/bin/bash
# Local Development Setup Script for SBV Pipeline
# This script sets up a complete local development environment

set -e  # Exit on error

echo "=================================="
echo "🚀 SBV Pipeline Local Setup"
echo "=================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker Desktop first.${NC}"
    echo "   Download from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not found.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is installed${NC}"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    if [ -f "sbv-pipeline/env.example" ]; then
        cp sbv-pipeline/env.example .env
        echo -e "${GREEN}✅ Created .env file. Please edit it with your API keys.${NC}"
        echo -e "${YELLOW}   Required: OPENAI_API_KEY${NC}"
        echo ""
        read -p "Press Enter after you've added your API keys to .env..."
    else
        echo -e "${RED}❌ env.example not found. Cannot create .env${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ .env file exists${NC}"
echo ""

# Step 1: Start Docker services
echo "📦 Starting Docker services (PostgreSQL, pgAdmin, Redis)..."
docker-compose up -d

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Check if PostgreSQL is healthy
max_retries=30
retry_count=0
while [ $retry_count -lt $max_retries ]; do
    if docker exec sbv_postgres pg_isready -U sbv_user -d sbv_db > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
        break
    fi
    retry_count=$((retry_count + 1))
    echo "   Attempt $retry_count/$max_retries..."
    sleep 2
done

if [ $retry_count -eq $max_retries ]; then
    echo -e "${RED}❌ PostgreSQL failed to start${NC}"
    exit 1
fi

echo ""

# Step 2: Set up Python virtual environment
echo "🐍 Setting up Python virtual environment..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Step 3: Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip > /dev/null
pip install -r sbv-pipeline/requirements.txt

echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 4: Update .env for local PostgreSQL
echo "🔧 Configuring .env for local PostgreSQL..."
if ! grep -q "DATABASE_URL=postgresql://sbv_user:sbv_password@localhost:5432/sbv_db" .env; then
    # Comment out any existing DATABASE_URL and add new one
    sed -i.bak 's/^DATABASE_URL=/#DATABASE_URL=/g' .env
    echo "" >> .env
    echo "# Local PostgreSQL (Docker)" >> .env
    echo "DATABASE_URL=postgresql://sbv_user:sbv_password@localhost:5432/sbv_db" >> .env
    echo -e "${GREEN}✅ .env updated for local PostgreSQL${NC}"
else
    echo -e "${GREEN}✅ .env already configured for PostgreSQL${NC}"
fi

echo ""

# Step 5: Initialize database
echo "🗄️  Initializing database..."
cd sbv-pipeline
python -c "from src.storage.database import init_db; init_db()"
cd ..

echo -e "${GREEN}✅ Database initialized${NC}"
echo ""

# Step 6: Verify setup
echo "🔍 Verifying setup..."
cd sbv-pipeline
python -c "
import sys
from src.config import settings
from src.storage.database import engine
from sqlalchemy import text

# Test database connection
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT version();'))
        version = result.fetchone()[0]
        print(f'✅ PostgreSQL connected: {version[:50]}...')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)

# Check API keys
if settings.openai_api_key:
    print('✅ OpenAI API key configured')
else:
    print('⚠️  OpenAI API key not found in .env')

print('✅ Setup verification complete')
" || exit 1

cd ..

echo ""
echo "=================================="
echo -e "${GREEN}🎉 Local setup complete!${NC}"
echo "=================================="
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Access pgAdmin (Database UI):"
echo "   🌐 http://localhost:5050"
echo "   📧 Email: alonof27@gmail.com"
echo "   🔑 Password: admin"
echo ""
echo "2. Run the dashboard:"
echo "   cd sbv-pipeline"
echo "   streamlit run src/dashboard/app.py"
echo ""
echo "3. Run an analysis:"
echo "   cd sbv-pipeline"
echo "   python -m src.main analyze data/input/example_companies.csv"
echo ""
echo "4. Stop services when done:"
echo "   docker-compose down"
echo ""
echo "=================================="

