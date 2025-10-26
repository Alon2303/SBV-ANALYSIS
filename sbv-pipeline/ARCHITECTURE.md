# SBV Pipeline Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                          │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   CLI Tool      │   REST API      │   Streamlit Dashboard       │
│   (Click)       │   (FastAPI)     │   (Interactive Viz)         │
└────────┬────────┴────────┬────────┴────────┬───────────────────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
         ┌─────────────────▼─────────────────┐
         │     ORCHESTRATOR LAYER             │
         │  - Job Manager                     │
         │  - Concurrent Processing           │
         │  - Progress Tracking               │
         └─────────────────┬─────────────────┘
                           │
         ┌─────────────────▼─────────────────┐
         │     SBV PROTOCOL ENGINE            │
         │  - Steps 0-8 Implementation        │
         │  - Research Coordination           │
         │  - Metric Calculation              │
         └─────────────────┬─────────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         │                                    │
         ▼                                    ▼
┌────────────────────┐            ┌────────────────────┐
│  RESEARCH AGENT    │            │  ANALYSIS ENGINE   │
│  - Web Scraping    │            │  - Constriction    │
│  - LLM Extraction  │            │  - Readiness       │
│  - Evidence Rating │            │  - Likely & Lovely │
└────────┬───────────┘            └──────────┬─────────┘
         │                                    │
         └─────────────────┬──────────────────┘
                           │
         ┌─────────────────▼─────────────────┐
         │     STORAGE LAYER                  │
         │  - PostgreSQL/SQLite               │
         │  - JSON Export                     │
         │  - Schema Validation               │
         └─────────────────┬─────────────────┘
                           │
         ┌─────────────────▼─────────────────┐
         │     EXPORT LAYER                   │
         │  - Google Sheets                   │
         │  - CSV/JSON Export                 │
         │  - PDF Reports (future)            │
         └────────────────────────────────────┘
```

## Component Details

### 1. Input Module (`src/input/`)

**Purpose**: Parse company lists from various file formats

**Components**:
- `parser.py`: CSV/TXT file parsing
- Validation and normalization

**Input Formats**:
- CSV: `company_name,homepage`
- TXT: One company per line

### 2. Research Agent (`src/research/`)

**Purpose**: AI-powered company research and data extraction

**Components**:
- `researcher.py`: Main research orchestrator
- `llm_client.py`: LLM API client (OpenAI/Anthropic)
- `web_scraper.py`: Playwright-based web scraping
- `prompts.py`: Prompt templates for structured extraction

**Process**:
1. Web search for company information
2. Scrape homepage and relevant URLs
3. LLM extraction of structured data:
   - Company description & value proposition
   - Technical claims with evidence
   - Social proof (accelerators, grants, customers)
   - Theory/literature references
4. Evidence strength assessment (1-5 scale)

**Key Prompts**:
- Company information extraction
- Bottleneck identification
- Readiness scoring (TRL/IRL/ORL/RCL)
- Likely & Lovely scoring (E/T/SP/LV)

### 3. Analysis Engine (`src/analysis/`)

**Purpose**: Implement SBV protocol calculations

**Components**:
- `protocol.py`: Main SBV orchestrator (Steps 0-8)
- `constriction.py`: Constriction Index (CI) calculation
- `readiness.py`: Readiness Index (RI) with Evidence Penalty
- `likely_lovely.py`: Likely & Lovely metrics
- `validator.py`: JSON schema validation

**Key Algorithms**:

#### Constriction Index (CI)
```python
S_norm = S / 35  # severity sum normalized
Md_norm = Md / 5  # median severity normalized
Mx_norm = Mx / 5  # max severity normalized
Cx_norm = Cx / 5  # complexity normalized

CI_fix = 0.4*S_norm + 0.3*Mx_norm + 0.2*Md_norm + 0.1*Cx_norm
```

#### Readiness Index (RI)
```python
# Geometric mean of adjusted readiness levels
RI = (TRL_adj/9 * IRL_adj/9 * ORL_adj/9 * RCL_adj/9)^0.25

# Evidence Penalty
p_unver = unverified_count / total_critical_claims
EP = 1 - (0.25 * p_unver)

RI_skeptical = RI * EP
RAR = RI_skeptical * CI_fix
```

#### Likely & Lovely
```python
LS_norm = (0.5*E + 0.25*T + 0.25*SP) / 5
LV_norm = LV / 5
CCF = LS_norm * LV_norm  # Claim Confidence Factor
```

### 4. Storage Layer (`src/storage/`)

**Purpose**: Persist analysis results

**Components**:
- `database.py`: SQLAlchemy engine and session management
- `db_models.py`: ORM models (Company, Analysis, Bottleneck, Citation)
- `repository.py`: CRUD operations and JSON export

**Database Schema**:
- `companies`: Company metadata
- `analyses`: Full SBV analysis results
- `bottlenecks`: Individual bottlenecks per analysis
- `citations`: Source citations per analysis

**Storage Options**:
- SQLite (default, standalone)
- PostgreSQL (production, Docker)

### 5. Orchestrator (`src/orchestrator/`)

**Purpose**: Manage concurrent analysis jobs

**Components**:
- `job_manager.py`: Job creation and processing
- Async/await for concurrency
- Progress tracking
- Error handling and retry logic

**Concurrency Model**:
- Semaphore-based rate limiting
- Configurable max concurrent analyses
- Background task processing (FastAPI)

### 6. API Layer (`src/api/`)

**Purpose**: REST API for programmatic access

**Components**:
- `app.py`: FastAPI application

**Endpoints**:
- `POST /api/analyze`: Submit companies for analysis
- `GET /api/status/{job_id}`: Check job status
- `GET /api/companies`: List all analyses
- `GET /api/companies/{id}`: Get detailed analysis
- `GET /api/companies/{id}/metrics`: Get specific metrics
- `POST /api/export`: Export to CSV/JSON

**Features**:
- CORS enabled
- Background task processing
- OpenAPI/Swagger documentation
- Dependency injection for database sessions

### 7. Dashboard (`src/dashboard/`)

**Purpose**: Interactive visualization and exploration

**Components**:
- `app.py`: Streamlit application

**Features**:
- Company list with sorting/filtering
- Interactive visualizations:
  - CI vs RI scatter plot
  - CCF ranking bar chart
  - Readiness components
  - Likely & Lovely radar charts
  - Comparative analysis
- Detailed company view
- CSV export
- Real-time data loading

**Visualization Libraries**:
- Plotly (interactive charts)
- Pandas (data manipulation)

### 8. Export Module (`src/export/`)

**Purpose**: Export results to external systems

**Components**:
- `google_sheets.py`: Google Sheets integration

**Features**:
- Automatic spreadsheet creation
- Formatted summary and detailed sheets
- Sharing via email
- Service account authentication

## Data Flow

### Analysis Pipeline

```
1. USER INPUT
   └─> companies.csv

2. PARSING
   └─> List[CompanyInput]

3. JOB CREATION
   └─> AnalysisJob with tasks

4. CONCURRENT PROCESSING
   For each company (parallel):
   
   5. RESEARCH PHASE
      ├─> Web scraping
      ├─> LLM extraction
      └─> Evidence assessment
      
   6. ANALYSIS PHASE
      ├─> Bottleneck identification
      ├─> Readiness scoring
      ├─> Likely & Lovely scoring
      ├─> CI calculation
      ├─> RI calculation
      └─> Final result assembly
      
   7. STORAGE PHASE
      ├─> Database insert
      ├─> JSON file export
      └─> Status update

8. RESULTS
   ├─> Database records
   ├─> JSON files
   └─> Dashboard visualization
```

### Technology Stack

**Backend**:
- Python 3.11+
- FastAPI (async web framework)
- SQLAlchemy (ORM)
- Pydantic (validation)

**AI/Research**:
- OpenAI GPT-4 or Anthropic Claude
- Playwright (web scraping)
- BeautifulSoup (HTML parsing)

**Data & Visualization**:
- Pandas (data manipulation)
- NumPy (numerical operations)
- Plotly (interactive charts)
- Streamlit (dashboard)

**Storage**:
- SQLite (development)
- PostgreSQL (production)
- JSON (export)

**Deployment**:
- Docker & Docker Compose
- Uvicorn (ASGI server)

## Configuration

**Environment Variables** (`.env`):
```bash
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Database
DATABASE_URL=sqlite:///./data/sbv.db

# Application
MAX_CONCURRENT_ANALYSES=10
LOG_LEVEL=INFO

# LLM Settings
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4-turbo-preview
TEMPERATURE=0.3
```

**Configuration Object** (`src/config.py`):
- Pydantic-based settings
- Environment variable loading
- Path management
- Type validation

## Scalability

**Horizontal Scaling**:
- Multiple API workers (Gunicorn/Uvicorn)
- Separate worker containers for analysis
- Shared PostgreSQL database
- Redis for job queue (optional)

**Vertical Scaling**:
- Increase `MAX_CONCURRENT_ANALYSES`
- More RAM for browser instances
- Faster LLM API (GPT-4 Turbo)

**Performance**:
- 1 company: ~1-2 minutes
- 10 companies: ~5-10 minutes (concurrent)
- 100 companies: ~30-60 minutes (concurrent)

**Bottlenecks**:
- LLM API rate limits
- Web scraping (Playwright overhead)
- Database writes (batching recommended)

## Extension Points

### Custom Metrics

Add new metrics in `src/analysis/`:
```python
# src/analysis/custom_metric.py
def calculate_custom_metric(data):
    # Your calculation
    return result
```

### Custom Prompts

Modify prompts in `src/research/prompts.py` to adjust AI behavior

### Custom Export Formats

Add exporters in `src/export/`:
```python
# src/export/pdf_exporter.py
class PDFExporter:
    def export(self, analysis):
        # Generate PDF report
        pass
```

### Database Extensions

Add fields to models in `src/storage/db_models.py` and run migrations

## Security Considerations

- API keys stored in environment variables (not in code)
- Database credentials in `.env` (gitignored)
- Google service account credentials separate
- CORS configured (restrict in production)
- No SQL injection (using ORM)
- Input validation (Pydantic)

## Testing

**Unit Tests** (`tests/test_analysis.py`):
- Metric calculations
- Input validation
- Edge cases

**Integration Tests** (TODO):
- End-to-end analysis pipeline
- Database operations
- API endpoints

**Run Tests**:
```bash
pytest tests/ -v
```

