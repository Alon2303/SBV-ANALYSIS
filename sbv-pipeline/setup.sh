#!/bin/bash
# Setup script for SBV Pipeline

set -e

echo "================================"
echo "SBV Pipeline Setup"
echo "================================"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
major=$(echo $python_version | cut -d. -f1)
minor=$(echo $python_version | cut -d. -f2)

echo "Detected Python version: $python_version"

if [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 11 ]); then
    echo "❌ Error: Python 3.11 or 3.12 is required"
    echo "   Current version: $python_version"
    echo "   Install Python 3.11: brew install python@3.11"
    exit 1
fi

if [ "$major" -eq 3 ] && [ "$minor" -ge 13 ]; then
    echo "⚠️  Warning: Python $python_version is too new"
    echo "   Many packages are not compatible with Python 3.13 yet"
    echo "   Recommended: Python 3.11 or 3.12"
    echo ""
    echo "To fix:"
    echo "  1. brew install python@3.11"
    echo "  2. Remove venv: rm -rf venv"
    echo "  3. Create new venv: python3.11 -m venv venv"
    echo "  4. Run this script again"
    echo ""
    read -p "Continue anyway? (not recommended) [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
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
echo "  (Using minimal requirements for SQLite mode)"
pip install -r requirements-minimal.txt
if [ $? -ne 0 ]; then
    echo "❌ Error installing dependencies"
    exit 1
fi
echo "✓ Dependencies installed"

# Install Playwright browsers
echo "Installing Playwright browsers..."
python -m playwright install chromium > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Error installing Playwright browsers"
    exit 1
fi
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

