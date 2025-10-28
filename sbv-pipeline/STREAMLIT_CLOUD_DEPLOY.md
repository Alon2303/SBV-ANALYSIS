# Deploying to Streamlit Cloud

## Quick Setup (Easiest)

### Option 1: Use `streamlit_app.py` (Recommended)

**Main file path:** `streamlit_app.py`

This is the simplest option - Streamlit Cloud automatically looks for this file.

### Option 2: Use direct path

**Main file path:** `src/dashboard/app.py`

---

## Step-by-Step Deployment

### 1. Prepare Your Repository

```bash
cd /Users/alonofir/Documents/P/sbv-pipeline

# Run some analyses locally to populate database
source venv/bin/activate
rm -f data/sbv.db
python -m src.main init
python -m src.main analyze data/input/example_companies.csv

# Add database to repo (for demo purposes)
git add data/sbv.db
git add streamlit_app.py
git add requirements-streamlit.txt

# Commit
git commit -m "Add Streamlit Cloud deployment files"

# Push
git push origin main
```

### 2. Deploy on Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. Click **"New app"**
4. Configure:
   - **Repository**: `Alon2303/SBV-ANALYSIS`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`
   - Click "Advanced settings"
   - **Python version**: `3.11`
5. Click **"Deploy!"**

### 3. Wait for Deployment

Streamlit Cloud will:
- Clone your repo
- Install dependencies from `requirements.txt`
- Start your app
- Give you a public URL like: `https://alon2303-sbv-analysis-streamlit-app-xyz123.streamlit.app/`

---

## Requirements File

Streamlit Cloud looks for `requirements.txt` in your repo root.

**The main `requirements.txt`** now includes both dashboard AND analysis dependencies:
- streamlit, plotly, pandas (dashboard)
- openai, anthropic (LLM for analysis)
- playwright, beautifulsoup4 (web scraping)
- sqlalchemy, pydantic (data management)

This allows users to run new analyses directly from the UI.

### System Dependencies

For web scraping with Playwright, you also need a `packages.txt` file:
```
chromium
chromium-driver
```

**Note**: Playwright on Streamlit Cloud may have limitations. The pipeline will automatically fall back to simpler HTTP scraping if Playwright fails.

---

## Important Notes

### Database

⚠️ **The dashboard reads from `data/sbv.db`**

You have two options:

**Option A: Include Pre-Populated Database** (For demo/read-only)
```bash
# Run analyses locally
python -m src.main analyze data/input/example_companies.csv

# Add database to git
git add data/sbv.db
git commit -m "Add sample analysis data"
git push
```

**Option B: Use Persistent Storage** (Advanced)
- Use Streamlit's file uploader to let users upload their own database
- Or connect to a cloud database (PostgreSQL on Railway, Heroku, etc.)

### Python Version

⚠️ **Must use Python 3.11 or 3.12** (NOT 3.13)

Set this in Advanced Settings when deploying.

### Secrets (Required for Analysis Feature)

**⚠️ REQUIRED** for running new analyses from the UI:

1. In Streamlit Cloud dashboard, go to your app settings
2. Click "Secrets"
3. Add your OpenAI API key:

```toml
OPENAI_API_KEY = "sk-proj-your-actual-key-here"
```

**Format Notes:**
- Use TOML format (not JSON)
- No quotes around the key name
- Include quotes around the value
- Each secret on its own line

**Without the API key**, users can still view existing analyses but cannot run new ones.

---

## Troubleshooting

### Error: "No module named 'src'"

**Fix**: Use `streamlit_app.py` as the main file (it adds `src` to the path)

### Error: "No such file or directory: 'data/sbv.db'"

**Fix**: Make sure you've committed the database file:
```bash
git add data/sbv.db
git commit -m "Add database"
git push
```

### Error: "Cannot import name X"

**Fix**: Check that `requirements-streamlit.txt` includes all needed packages

### Dashboard shows "No analyses found"

**Fix**: The database is empty. Run analyses locally and commit the populated database.

---

## Read-Only Demo vs Full Pipeline

### Dashboard Only (Read-Only)
- **What it does**: Displays pre-analyzed data
- **Requirements**: Minimal (`requirements-streamlit.txt`)
- **Database**: Include pre-populated `data/sbv.db`
- **Cost**: Free on Streamlit Cloud
- **Best for**: Sharing results with stakeholders

### Full Pipeline (Analysis + Dashboard)
- **What it does**: Users can submit companies for analysis
- **Requirements**: Full (`requirements.txt` or `requirements-minimal.txt`)
- **Database**: Persistent storage needed
- **Cost**: May exceed Streamlit Cloud free tier
- **Best for**: Internal tools, not public demos

**Recommendation**: Deploy dashboard-only for public sharing.

---

## Custom Domain (Optional)

After deployment, you can:
1. Get a custom domain (e.g., `sbv-analysis.yourcompany.com`)
2. Configure in Streamlit Cloud settings
3. Point your DNS CNAME to Streamlit

---

## File Checklist

Before deploying, make sure these files are in your repo:

- ✅ `streamlit_app.py` (entry point)
- ✅ `requirements.txt` or `requirements-streamlit.txt` (dependencies)
- ✅ `src/dashboard/app.py` (dashboard code)
- ✅ `data/sbv.db` (pre-populated database)
- ✅ `.gitignore` (don't commit `.env`, `venv/`, `__pycache__/`)

---

## Example Public URLs

Your deployed app will be accessible at:
```
https://<username>-<repo-name>-<branch>-<random>.streamlit.app/
```

Example:
```
https://alon2303-sbv-analysis-main-streamlit-app.streamlit.app/
```

---

## Support

For Streamlit Cloud issues:
- Docs: https://docs.streamlit.io/streamlit-community-cloud
- Forum: https://discuss.streamlit.io/
- Status: https://streamlit.statuspage.io/

For SBV Pipeline issues:
- Check README.md
- Check QUICKSTART.md
- Review logs in Streamlit Cloud dashboard

