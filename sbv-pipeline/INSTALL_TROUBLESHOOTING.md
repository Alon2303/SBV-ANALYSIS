# Installation Troubleshooting

## Common Installation Issues

### Issue 1: PostgreSQL Error (`psycopg2-binary` fails)

**Error:**
```
Error: pg_config executable not found.
```

**Solution:**
Use the minimal requirements file (SQLite only):

```bash
pip install -r requirements-minimal.txt
playwright install chromium
```

**Why:** The default `requirements.txt` includes PostgreSQL support for production deployments. For standalone/development mode with SQLite, you don't need it.

If you DO need PostgreSQL later:
```bash
# Install PostgreSQL first
brew install postgresql

# Then install PostgreSQL Python adapter
pip install -r requirements-postgresql.txt
```

---

### Issue 2: Python 3.13 Compatibility ⚠️ COMMON ISSUE

**Error:**
```
TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'
Failed to build pydantic-core, tiktoken, matplotlib
```

**Cause:** Python 3.13 is too new (released Oct 2024). Many packages haven't updated yet.

**Solution:**
Use Python 3.11 or 3.12 instead:

```bash
# Install Python 3.11
brew install python@3.11

# Remove old virtual environment
cd /Users/alonofir/Documents/P/sbv-pipeline
rm -rf venv

# Create new venv with Python 3.11
python3.11 -m venv venv
source venv/bin/activate

# Verify version (should be 3.11.x)
python --version

# Install requirements
pip install --upgrade pip
pip install -r requirements-minimal.txt
python -m playwright install chromium
```

**See also:** `PYTHON_VERSION_FIX.md` for detailed instructions

---

### Issue 3: Playwright Install Fails

**Error:**
```
playwright: command not found
```

**Solution:**
Install Python packages first, THEN Playwright browsers:

```bash
# Step 1: Install Python packages
pip install -r requirements-minimal.txt

# Step 2: Install Playwright browsers
python -m playwright install chromium
```

**Note:** Use `python -m playwright` instead of just `playwright`.

---

### Issue 4: Google Sheets Optional Dependencies

If you don't need Google Sheets export, you can skip those dependencies. They're commented out in `requirements-minimal.txt`.

To enable Google Sheets:
```bash
pip install gspread google-auth oauth2client
```

---

### Issue 5: Jupyter Optional Dependencies

If you don't need Jupyter notebooks, skip those dependencies (commented out in `requirements-minimal.txt`).

To enable Jupyter:
```bash
pip install jupyter ipykernel ipywidgets
```

---

## Quick Install Guide (Recommended)

### For SQLite Mode (Standalone - MacBook)

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install minimal requirements (SQLite only)
pip install -r requirements-minimal.txt

# 3. Install Playwright browsers
python -m playwright install chromium

# 4. Initialize database
python -m src.main init

# 5. Verify installation
python verify_setup.py
```

### For PostgreSQL Mode (Production - Docker)

Use Docker instead:
```bash
docker-compose up -d
```

Docker handles all dependencies automatically.

---

## Installation Verification

After installation, verify everything works:

```bash
# Check installation
python verify_setup.py

# Test imports
python -c "import fastapi, streamlit, openai, playwright; print('✓ All imports successful')"

# Run tests
pytest tests/ -v
```

---

## Platform-Specific Notes

### macOS (M1/M2/M3/M4)

Some packages may need Rosetta or native ARM builds:

```bash
# If issues with numpy/pandas, try:
pip install --upgrade --force-reinstall numpy pandas
```

### macOS with Homebrew Python

If using Homebrew Python:

```bash
# Ensure you're using the right Python
which python3
python3 --version

# Should be Python 3.11+ from Homebrew
```

---

## Minimal Test

Once installed, test with a simple analysis:

```bash
source venv/bin/activate

# Test database
python -c "from src.storage import init_db; init_db(); print('✓ Database OK')"

# Test LLM client
python -c "from src.research import LLMClient; print('✓ LLM client OK')"

# Test config
python -c "from src.config import settings; print(f'✓ Config OK: {settings.database_url}')"
```

---

## Clean Slate

If all else fails, start fresh:

```bash
# Remove virtual environment
rm -rf venv

# Remove any cached files
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# Start over
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-minimal.txt
python -m playwright install chromium
```

---

## Getting Help

If you still have issues:

1. Check Python version: `python --version` (should be 3.11+)
2. Check pip version: `pip --version`
3. Check virtual environment is active: `which python` (should show path with `venv`)
4. Review error messages carefully
5. Search the error on GitHub issues for the specific package

## Contact

For package-specific issues:
- FastAPI: https://github.com/tiangolo/fastapi
- Streamlit: https://github.com/streamlit/streamlit
- Playwright: https://github.com/microsoft/playwright-python
- OpenAI: https://github.com/openai/openai-python

