# Quick Fix for Installation Errors

## Problem 1: Python 3.13 (Most Common)

**Error:** `Failed to build pydantic-core` or `TypeError: ForwardRef._evaluate()`

**Solution:** Use Python 3.11 or 3.12 instead of 3.13

```bash
# Install Python 3.11
brew install python@3.11

# Remove old venv
cd /Users/alonofir/Documents/P/sbv-pipeline
rm -rf venv

# Create new venv with Python 3.11
python3.11 -m venv venv
source venv/bin/activate

# Verify (should show 3.11.x)
python --version

# Continue with installation below
```

## Problem 2: PostgreSQL Error

**Error:** `pg_config executable not found`

**Solution:** Use minimal requirements (SQLite only)

## Complete Installation Steps

```bash
cd /Users/alonofir/Documents/P/sbv-pipeline

# Activate virtual environment (create if needed)
python3 -m venv venv
source venv/bin/activate

# Install MINIMAL requirements (SQLite only, no PostgreSQL)
pip install -r requirements-minimal.txt

# Install Playwright browsers using python module
python -m playwright install chromium

# Initialize database
python -m src.main init

# Verify installation
python verify_setup.py
```

## What Changed?

- **requirements-minimal.txt** = SQLite only (no PostgreSQL)
- **requirements.txt** = Full version with PostgreSQL (for Docker/production)

For standalone mode on your MacBook, you only need `requirements-minimal.txt`.

## Test It Works

```bash
# Add your API key
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# Run example analysis
python -m src.main analyze data/input/example_companies.csv

# Launch dashboard
python -m src.main dashboard
```

## Still Having Issues?

See `INSTALL_TROUBLESHOOTING.md` for detailed solutions.

