# SBV Analysis Pipeline - Project Summary

## Overview

The **SBV Analysis Pipeline** is a production-ready AI-powered system for analyzing early-stage companies using the Strategic Bottleneck Validation (SBV) protocol. It automates research, applies sophisticated metrics, and provides interactive visualizations.

## Key Features

✅ **AI-Powered Research**: Automated company research using GPT-4/Claude  
✅ **SBV Protocol**: Complete implementation with CI, RI, and Likely & Lovely metrics  
✅ **Concurrent Processing**: Analyze 1-100+ companies in parallel  
✅ **Interactive Dashboard**: Streamlit-based UI with Plotly charts  
✅ **REST API**: FastAPI server for programmatic access  
✅ **Multiple Storage**: SQLite (dev) + PostgreSQL (prod) + JSON export  
✅ **Google Sheets**: Export results for sharing  
✅ **Docker Support**: Containerized deployment  
✅ **Jupyter Notebooks**: Interactive analysis and exploration  

## What It Does

### Input
- CSV or TXT file with company names (1-100+ companies)
- Optional: homepage URLs for faster research

### Process
1. **Research Phase**: AI scrapes web, extracts structured data
2. **Analysis Phase**: Applies SBV protocol, calculates metrics
3. **Storage Phase**: Saves to database + exports JSON

### Output
- **Database**: Full analysis results in SQLite/PostgreSQL
- **JSON Files**: Schema-compliant exports for each company
- **Dashboard**: Interactive visualization with:
  - Company list (sortable/filterable)
  - CI vs RI scatter plots
  - CCF rankings
  - Readiness components
  - Likely & Lovely radar charts
  - Detailed company views
  - Comparative analysis

## Metrics Calculated

### Constriction Index (CI)
Measures bottleneck severity across:
- Technical challenges
- Market adoption barriers
- Regulatory hurdles
- Economic constraints
- Capital needs

**Formula**: Weighted average of S (severity sum), Md (median), Mx (max), Cx (complexity)

### Readiness Index (RI)
Composite readiness score:
- **TRL** (Technology Readiness Level, 1-9)
- **IRL** (Integration Readiness Level, 1-9)
- **ORL** (Operations Readiness Level, 1-9)
- **RCL** (Regulatory/Compliance Level, 1-9)

**With skeptical discount**: RI_skeptical = RI × EP (Evidence Penalty)

### Likely & Lovely
- **E** (Evidence, 1-5): Quality of supporting evidence
- **T** (Theory, 1-5): Theoretical grounding
- **SP** (Social Proof, 1-5): Credibility markers
- **LV** (Lovely, 1-5): Desirability/impact if true
- **CCF** (Claim Confidence Factor): LS_norm × LV_norm

### Risk Metrics
- **RAR** (Readiness-Adjusted Risk): RI_skeptical × CI_fix
- **EP** (Evidence Penalty): Skeptical discount for unverified claims

## Technology Stack

**Language**: Python 3.11+

**Core Frameworks**:
- FastAPI (REST API)
- Streamlit (Dashboard)
- SQLAlchemy (ORM)
- Pydantic (Validation)

**AI/Research**:
- OpenAI GPT-4 or Anthropic Claude
- Playwright (Web scraping)
- BeautifulSoup (HTML parsing)

**Data/Viz**:
- Pandas, NumPy
- Plotly (Interactive charts)

**Deployment**:
- Docker & Docker Compose
- PostgreSQL (production)
- SQLite (development)

## Project Structure

```
sbv-pipeline/
├── src/
│   ├── analysis/          # SBV protocol implementation
│   │   ├── protocol.py           # Main orchestrator
│   │   ├── constriction.py       # CI calculation
│   │   ├── readiness.py          # RI calculation
│   │   ├── likely_lovely.py      # Likely & Lovely
│   │   └── validator.py          # Schema validation
│   ├── research/          # AI research agent
│   │   ├── researcher.py         # Research orchestrator
│   │   ├── llm_client.py         # OpenAI/Anthropic client
│   │   ├── web_scraper.py        # Playwright scraping
│   │   └── prompts.py            # LLM prompts
│   ├── storage/           # Database layer
│   │   ├── database.py           # SQLAlchemy setup
│   │   ├── db_models.py          # ORM models
│   │   └── repository.py         # CRUD operations
│   ├── orchestrator/      # Job management
│   │   └── job_manager.py        # Concurrent processing
│   ├── input/             # File parsing
│   │   └── parser.py             # CSV/TXT parser
│   ├── api/               # REST API
│   │   └── app.py                # FastAPI application
│   ├── dashboard/         # Streamlit UI
│   │   └── app.py                # Dashboard application
│   ├── export/            # Export utilities
│   │   └── google_sheets.py      # Google Sheets integration
│   ├── config.py          # Configuration
│   └── main.py            # CLI entry point
├── notebooks/             # Jupyter analysis
│   ├── 01_exploratory_analysis.ipynb
│   └── 02_cohort_comparison.ipynb
├── tests/                 # Unit tests
│   └── test_analysis.py
├── data/                  # Data directories
│   ├── input/            # Input CSVs
│   └── output/           # JSON results
├── schemas/              # JSON schema
│   └── sbv_tiny_schema.json
├── Dockerfile            # Docker image
├── docker-compose.yml    # Docker Compose config
├── requirements.txt      # Python dependencies
├── Makefile             # Build commands
├── setup.sh             # Setup script
├── README.md            # Main documentation
├── QUICKSTART.md        # Quick start guide
├── ARCHITECTURE.md      # Architecture details
└── .env.example         # Environment template
```

## Quick Start

### 1. Setup (One-time)

```bash
cd /Users/alonofir/Documents/P/sbv-pipeline
./setup.sh
```

### 2. Configure

Add your API key to `.env`:
```bash
OPENAI_API_KEY=sk-your-key-here
```

### 3. Run Analysis

```bash
# Activate virtual environment
source venv/bin/activate

# Analyze companies
python -m src.main analyze data/input/example_companies.csv

# Launch dashboard
python -m src.main dashboard
```

## Usage Modes

### Mode 1: CLI (Batch Processing)

```bash
# Analyze from CSV
python -m src.main analyze companies.csv

# View dashboard
python -m src.main dashboard

# Using Makefile
make analyze
make run-dashboard
```

### Mode 2: REST API (Programmatic)

```bash
# Start API server
make run-api
# OR
uvicorn src.api.app:app --reload

# Submit analysis (via curl, Python, etc.)
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"companies": [{"company_name": "Dynami Battery Corp"}]}'

# Check status
curl http://localhost:8000/api/status/{job_id}

# Get results
curl http://localhost:8000/api/companies
```

### Mode 3: Docker (Production)

```bash
# Build and start
make docker-up
# OR
docker-compose up -d

# Access
# API: http://localhost:8000
# Dashboard: http://localhost:8501
```

### Mode 4: Jupyter (Interactive)

```bash
make jupyter
# OR
jupyter notebook notebooks/
```

## Performance

| Companies | Time (Concurrent) | Cost (GPT-4) |
|-----------|-------------------|--------------|
| 1         | ~1-2 min          | ~$0.50-1.50  |
| 10        | ~5-10 min         | ~$5-15       |
| 100       | ~30-60 min        | ~$50-155     |

**Hardware**: Tested on MacBook Pro M4 with 24GB RAM

## Output Examples

### JSON Output (per company)

Conforms to `sbv_tiny_schema.json`:

```json
{
  "company": "Dynami Battery Corp",
  "homepage": "https://dynami-battery.com/",
  "as_of_date": "2025-10-26",
  "constriction": {
    "CI_fix": 0.788,
    "k": 7,
    "S": 29,
    "Md": 4.0,
    "Mx": 5.0
  },
  "readiness": {
    "RI": 0.344,
    "RI_skeptical": 0.279,
    "EP": 0.813,
    "RAR": 0.059
  },
  "likely_lovely": {
    "E": 2,
    "T": 4,
    "SP": 3,
    "CCF": 0.44
  },
  "bottlenecks": [...],
  "citations": [...]
}
```

### Dashboard Views

1. **Company List**: Sortable table with all metrics
2. **Visualizations**: 
   - CI vs RI scatter (size = CCF, color = RAR)
   - CCF ranking bar chart
   - Readiness components
   - Likely & Lovely radar
3. **Detailed Analysis**: Full company breakdown
4. **Comparative Analysis**: Multi-company comparison

## Testing

```bash
# Run unit tests
make test
# OR
pytest tests/ -v

# Test specific module
pytest tests/test_analysis.py -v
```

## Extending the System

### Add Custom Metrics

```python
# src/analysis/custom_metric.py
def calculate_custom_metric(data):
    # Your calculation
    return result
```

### Modify LLM Prompts

Edit `src/research/prompts.py` to tune AI behavior

### Add Export Formats

```python
# src/export/pdf_exporter.py
class PDFExporter:
    def export(self, analysis):
        # Generate PDF
        pass
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Playwright not found | `playwright install chromium` |
| OpenAI rate limit | Reduce `MAX_CONCURRENT_ANALYSES` |
| No results in dashboard | Check `data/sbv.db` and analysis status |
| Import errors | Activate venv: `source venv/bin/activate` |

## Documentation

- **README.md**: Main documentation
- **QUICKSTART.md**: Quick start guide with examples
- **ARCHITECTURE.md**: System architecture and design
- **API Docs**: http://localhost:8000/docs (when API running)

## Future Enhancements

- [ ] PDF report generation
- [ ] Human-in-the-loop review mode
- [ ] Cohort normalization (compare across batch)
- [ ] Advanced LLM chain-of-thought prompting
- [ ] Redis-based job queue for distributed processing
- [ ] Real-time progress updates via WebSocket
- [ ] Custom ML models for metric prediction
- [ ] Integration with CrunchBase/PitchBook APIs

## Support

For issues or questions:
1. Check documentation (README.md, QUICKSTART.md, ARCHITECTURE.md)
2. Review example output: `data/output/dynami_battery_corp_*.json`
3. Examine source code in `src/`
4. Run tests to verify installation: `make test`

## License

MIT License - See LICENSE file for details

## Authors

Built according to the SBV protocol specification with Likely & Lovely extensions.

---

**Ready to analyze companies at scale!** 🚀

