# SBV Pipeline - Quick Start Guide

## Prerequisites

- Python 3.11+
- OpenAI API key or Anthropic API key
- 8GB+ RAM (for concurrent processing)

## Installation

### 1. Clone/Setup Repository

```bash
cd /Users/alonofir/Documents/P/sbv-pipeline
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Configure Environment

```bash
cp env.example .env
# Edit .env and add your API keys
```

Required environment variables:
```
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

### Method 1: CLI (Recommended for Batch Processing)

#### Step 1: Prepare Input File

Create a CSV file with company names:

```csv
company_name,homepage
Dynami Battery Corp,https://dynami-battery.com/
QuantumScape,https://www.quantumscape.com/
Sila Nanotechnologies,https://silanano.com/
```

Save as `data/input/my_companies.csv`

#### Step 2: Run Analysis

```bash
python -m src.main analyze data/input/my_companies.csv
```

This will:
- Research each company using AI
- Apply SBV protocol
- Calculate CI, RI, Likely/Lovely metrics
- Save results to database and JSON files

#### Step 3: View Results

Launch the dashboard:

```bash
python -m src.main dashboard
```

Or directly:

```bash
streamlit run src/dashboard/app.py
```

Open browser to `http://localhost:8501`

### Method 2: API Server (For Programmatic Access)

#### Start the API server:

```bash
uvicorn src.api.app:app --reload
```

API will be available at `http://localhost:8000`

#### Submit analysis via API:

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "companies": [
      {"company_name": "Dynami Battery Corp", "homepage": "https://dynami-battery.com/"}
    ]
  }'
```

Response:
```json
{
  "job_id": "abc-123-xyz",
  "status": "processing",
  "total": 1,
  "completed": 0,
  ...
}
```

#### Check status:

```bash
curl http://localhost:8000/api/status/abc-123-xyz
```

#### Get results:

```bash
curl http://localhost:8000/api/companies
```

### Method 3: Docker (Production Deployment)

#### Build and run with Docker Compose:

```bash
docker-compose up -d
```

This starts:
- PostgreSQL database (port 5432)
- API server (port 8000)
- Dashboard (port 8501)

Access:
- API: http://localhost:8000
- Dashboard: http://localhost:8501
- API Docs: http://localhost:8000/docs

## Output Locations

- **Database**: `data/sbv.db` (SQLite) or PostgreSQL
- **JSON files**: `data/output/{company_name}_{date}.json`
- **Dashboard**: http://localhost:8501

## Example Workflow

```bash
# 1. Initialize database
python -m src.main init

# 2. Analyze companies
python -m src.main analyze data/input/example_companies.csv

# 3. View dashboard
python -m src.main dashboard

# 4. Export results
# Via API:
curl http://localhost:8000/api/export?format=csv

# Via dashboard: Click "Download CSV" button
```

## Google Sheets Integration

To export results to Google Sheets:

1. Create a Google Cloud service account
2. Download credentials JSON
3. Save to `credentials/google-service-account.json`
4. Update `.env`:
   ```
   GOOGLE_SHEETS_CREDENTIALS_PATH=./credentials/google-service-account.json
   ```

5. Use the API or add to your code:

```python
from src.export import GoogleSheetsExporter
from src.storage import get_db, AnalysisRepository

with get_db() as db:
    repo = AnalysisRepository(db)
    analyses = repo.list_analyses()
    
    data = [repo.export_to_json(a) for a in analyses]
    
    exporter = GoogleSheetsExporter("credentials/google-service-account.json")
    url = exporter.export_analyses(data, "SBV Results", share_email="you@example.com")
    print(f"Exported to: {url}")
```

## Jupyter Notebooks

Interactive analysis notebooks are in `notebooks/`:

```bash
jupyter notebook notebooks/01_exploratory_analysis.ipynb
```

## Troubleshooting

### Issue: Playwright browser not found

```bash
playwright install chromium
```

### Issue: OpenAI API rate limit

Reduce concurrent analyses in `.env`:
```
MAX_CONCURRENT_ANALYSES=5
```

### Issue: No results in dashboard

Check analysis status:
```bash
sqlite3 data/sbv.db "SELECT company.name, status FROM analyses JOIN companies company ON analyses.company_id = company.id;"
```

### Issue: LLM producing poor results

- Try different model: Set `DEFAULT_MODEL=gpt-4` in `.env`
- Adjust temperature: Set `TEMPERATURE=0.1` for more deterministic
- Check prompt templates in `src/research/prompts.py`

## Performance Notes

- **1 company**: ~1-2 minutes
- **10 companies**: ~5-10 minutes (concurrent)
- **100 companies**: ~30-60 minutes (concurrent)

Cost: ~$0.50-1.50 per company (GPT-4)

## Next Steps

1. **Validate on known companies**: Compare results to manual analysis
2. **Tune prompts**: Adjust scoring in `src/research/prompts.py`
3. **Add custom metrics**: Extend `src/analysis/` modules
4. **Build reports**: Create PDF export from JSON results

## Support

- Check `README.md` for architecture details
- Review `src/` code for implementation
- See example JSON: `data/output/dynami_battery_corp_*.json`

