# SBV Company Analysis Pipeline

> **AI-powered analysis engine implementing the Strategic Bottleneck Validation (SBV) protocol with Constriction Index, Readiness Index, and Likely & Lovely metrics**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

The SBV Analysis Pipeline is a production-ready system that automates the analysis of early-stage technology companies. It combines AI-powered research with sophisticated metrics to provide:

- **Quantitative Scoring**: Constriction Index (CI), Readiness Index (RI), Claim Confidence Factor (CCF)
- **Evidence-Based Analysis**: Skeptical evaluation with verification scoring
- **Scalable Processing**: Analyze 100+ companies concurrently
- **Interactive Visualization**: Explore results through web dashboards

**Perfect for**: Investors, accelerators, grant programs, technology scouts, and research teams evaluating climate tech, advanced materials, and deep tech companies.

## ✨ Key Features

- 🤖 **AI-Powered Research**: Automated company research using GPT-4/Claude and web scraping
- 📊 **SBV Protocol**: Complete implementation of Steps 0-8 with CI, RI, and Likely/Lovely calculations
- ⚡ **Concurrent Processing**: Analyze 1-100+ companies in parallel
- 📈 **Interactive Dashboard**: Streamlit-based visualization with Plotly charts
- 🔌 **REST API**: FastAPI server for programmatic access
- 💾 **Multiple Storage**: SQLite (standalone) + PostgreSQL (production) + JSON export
- 📑 **Google Sheets**: Export and share results with stakeholders
- 🐳 **Docker Support**: Containerized deployment for production

## 🚀 Quick Start

> ⚠️ **Important:** Use Python 3.11 or 3.12 (NOT 3.13). If you have Python 3.13, see [`PYTHON_VERSION_FIX.md`](PYTHON_VERSION_FIX.md) first.

### One-Command Setup

```bash
cd /Users/alonofir/Documents/P/sbv-pipeline

# Check Python version (should be 3.11.x or 3.12.x)
python3 --version

# If you need Python 3.11:
# brew install python@3.11
# python3.11 -m venv venv && source venv/bin/activate

./setup.sh
```

This script:
- ✅ Creates virtual environment
- ✅ Installs all dependencies
- ✅ Sets up Playwright browsers
- ✅ Initializes database
- ✅ Creates data directories

### Configure API Keys

Edit `.env` and add your API key:

```bash
# OpenAI (recommended)
OPENAI_API_KEY=sk-your-key-here

# OR Anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Run Your First Analysis

```bash
# Activate environment
source venv/bin/activate

# Analyze example company
python -m src.main analyze data/input/example_companies.csv

# View results in dashboard
python -m src.main dashboard
```

Open browser to `http://localhost:8501` to explore results!

### Using Make (Recommended)

```bash
make setup          # Initial setup
make analyze        # Run example analysis
make run-dashboard  # Launch dashboard
make help          # See all commands
```

### Docker Mode

```bash
docker-compose up -d
# API: http://localhost:8000
# Dashboard: http://localhost:8501
```

## Architecture

- **Research Agent**: Web scraping + LLM-based data extraction
- **Analysis Engine**: SBV protocol with CI/RI/Likely/Lovely calculations
- **Storage Layer**: SQLAlchemy ORM + JSON export
- **API**: FastAPI REST endpoints
- **Dashboard**: Streamlit with Plotly visualizations
- **Notebooks**: Jupyter for custom analysis

## API Endpoints

- `POST /api/analyze` - Submit company list
- `GET /api/status/{job_id}` - Check progress
- `GET /api/companies` - List all analyses
- `GET /api/companies/{id}` - Get detailed results
- `POST /api/export` - Export to CSV/Google Sheets

## Project Structure

```
sbv-pipeline/
├── src/
│   ├── input/          # CSV parsing
│   ├── research/       # AI research agent
│   ├── analysis/       # SBV protocol implementation
│   ├── storage/        # Database models
│   ├── orchestrator/   # Job processing
│   ├── api/           # FastAPI endpoints
│   ├── dashboard/     # Streamlit UI
│   ├── config.py      # Settings
│   └── main.py        # CLI entry point
├── notebooks/         # Jupyter analysis
├── schemas/          # JSON schema
├── data/
│   ├── input/        # Input CSVs
│   └── output/       # Results (JSON + CSV)
├── tests/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 💰 Cost & Performance

| Companies | Time (Concurrent) | Cost (GPT-4) |
|-----------|-------------------|--------------|
| 1         | ~1-2 min          | ~$0.50-1.50  |
| 10        | ~5-10 min         | ~$5-15       |
| 100       | ~30-60 min        | ~$50-155     |

*Tested on MacBook Pro M4 with 24GB RAM*

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)**: Detailed usage guide with examples
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: System architecture and technical design
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)**: High-level overview
- **API Docs**: http://localhost:8000/docs (when API is running)

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
pytest tests/ -v --cov=src

# Test specific module
pytest tests/test_analysis.py -v
```

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Playwright not found | Run `playwright install chromium` |
| OpenAI rate limit | Reduce `MAX_CONCURRENT_ANALYSES=5` in `.env` |
| No results in dashboard | Check `data/sbv.db` with `sqlite3` |
| Import errors | Activate venv: `source venv/bin/activate` |

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

Built according to the SBV protocol specification with Likely & Lovely extensions, incorporating:
- Technology Readiness Levels (TRL) framework
- Evidence-based skeptical evaluation
- Strategic bottleneck identification methodology

---

**Questions?** Check the documentation or open an issue!

**Ready to analyze?** Run `./setup.sh` to get started! 🚀

