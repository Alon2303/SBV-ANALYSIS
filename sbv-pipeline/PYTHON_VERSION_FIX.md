# Python Version Fix

## Problem

You're using Python 3.13, which is too new. Many packages haven't been updated yet.

**Error:**
```
TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'
Failed to build pydantic-core
```

## Solution: Use Python 3.11 or 3.12

### Option 1: Install Python 3.11 with Homebrew (Recommended)

```bash
# Install Python 3.11
brew install python@3.11

# Remove old virtual environment
cd /Users/alonofir/Documents/P/sbv-pipeline
rm -rf venv

# Create new venv with Python 3.11
python3.11 -m venv venv

# Activate it
source venv/bin/activate

# Verify version (should show 3.11.x)
python --version

# Now install requirements
pip install --upgrade pip
pip install -r requirements-minimal.txt
python -m playwright install chromium
```

### Option 2: Use pyenv (If you have it)

```bash
# Install Python 3.11
pyenv install 3.11.7

# Set local version for this project
cd /Users/alonofir/Documents/P/sbv-pipeline
pyenv local 3.11.7

# Remove old venv
rm -rf venv

# Create new venv
python -m venv venv
source venv/bin/activate

# Install
pip install --upgrade pip
pip install -r requirements-minimal.txt
python -m playwright install chromium
```

### Option 3: Use Python 3.12

If you have Python 3.12 instead:

```bash
# Install Python 3.12
brew install python@3.12

# Remove old venv
cd /Users/alonofir/Documents/P/sbv-pipeline
rm -rf venv

# Create new venv
python3.12 -m venv venv
source venv/bin/activate

# Install
pip install --upgrade pip
pip install -r requirements-minimal.txt
python -m playwright install chromium
```

## Check Python Version

```bash
# Check available Python versions
ls /usr/local/bin/python*

# OR with Homebrew
brew list | grep python

# Check current version
python --version
python3 --version
python3.11 --version
python3.12 --version
```

## After Installing Python 3.11/3.12

```bash
cd /Users/alonofir/Documents/P/sbv-pipeline

# Remove old venv
rm -rf venv

# Create new venv with Python 3.11 or 3.12
python3.11 -m venv venv
# OR
python3.12 -m venv venv

# Activate
source venv/bin/activate

# Verify (should show 3.11.x or 3.12.x)
python --version

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements-minimal.txt

# Install Playwright
python -m playwright install chromium

# Initialize database
python -m src.main init

# Verify installation
python verify_setup.py
```

## Why Not Python 3.13?

Python 3.13 was just released (October 2024), and many popular packages haven't updated yet:
- `pydantic-core` (used by FastAPI)
- `tiktoken` (used by OpenAI)
- `matplotlib` (visualization)

**Use Python 3.11 or 3.12** - they're stable and fully supported by all packages.

## Success Check

After switching to Python 3.11/3.12, you should see:

```bash
✓ All packages install without errors
✓ python --version shows 3.11.x or 3.12.x
✓ python verify_setup.py passes all checks
```

