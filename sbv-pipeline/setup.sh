#!/bin/bash
# Setup script for SBV Pipeline

set -e

echo "================================"
echo "SBV Pipeline Setup"
echo "================================"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
required_version="3.11"

if (( $(echo "$python_version < $required_version" | bc -l) )); then
    echo "❌ Error: Python $required_version or higher is required"
    echo "   Current version: $python_version"
    exit 1
fi

echo "✓ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ pip upgraded"

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1
echo "✓ Dependencies installed"

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium > /dev/null 2>&1
echo "✓ Playwright browsers installed"

# Create directories
echo "Creating data directories..."
mkdir -p data/input data/output schemas credentials
echo "✓ Directories created"

# Copy environment file if not exists
if [ ! -f ".env" ]; then
    cp env.example .env
    echo "✓ Created .env file (please add your API keys)"
else
    echo "✓ .env file exists"
fi

# Initialize database
echo "Initializing database..."
python -m src.main init > /dev/null 2>&1
echo "✓ Database initialized"

echo ""
echo "================================"
echo "Setup Complete! 🎉"
echo "================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Add your API key to .env:"
echo "   export OPENAI_API_KEY='your-key-here'"
echo "   # OR"
echo "   export ANTHROPIC_API_KEY='your-key-here'"
echo ""
echo "2. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "3. Run analysis:"
echo "   python -m src.main analyze data/input/example_companies.csv"
echo ""
echo "4. Launch dashboard:"
echo "   python -m src.main dashboard"
echo ""
echo "See QUICKSTART.md for detailed usage instructions."
echo ""

