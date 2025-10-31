# Modular Data Sources Implementation Plan

## 📊 Database Decision Matrix

### Option 1: SQLite + GitHub (RECOMMENDED for Streamlit Cloud)
✅ **Pros:**
- ✅ FREE - No hosting costs
- ✅ Works perfectly on Streamlit Cloud
- ✅ Can commit to GitHub (if DB < 100MB)
- ✅ Simple backup (just copy .db file)
- ✅ No connection credentials needed
- ✅ Fast for < 10,000 companies

❌ **Cons:**
- ❌ Single-file locking (not ideal for high concurrency)
- ❌ Limited to ~100MB on GitHub
- ❌ Resets on Streamlit Cloud reboot (unless backed up to external storage)

### Option 2: PostgreSQL + External Hosting (Railway, Supabase, Neon)
✅ **Pros:**
- ✅ Streamlit Cloud compatible
- ✅ True persistent storage (survives reboots)
- ✅ Concurrent writes
- ✅ Scalable to millions of records
- ✅ Free tiers available (Railway: $5/month, Supabase: free tier exists)

❌ **Cons:**
- ❌ $5-20/month cost
- ❌ Requires connection credentials
- ❌ Network latency

### Option 3: MySQL + PlanetScale/AWS RDS
✅ **Pros:**
- ✅ As requested by user
- ✅ Serverless options (PlanetScale)
- ✅ Persistent storage

❌ **Cons:**
- ❌ $10-30/month
- ❌ More complex setup
- ❌ PlanetScale discontinued free tier

---

## 🎯 RECOMMENDED APPROACH

**Hybrid Strategy:**
1. **Local Development**: SQLite (easy testing)
2. **Streamlit Cloud**: PostgreSQL on Railway/Supabase (persistent)
3. **Backup Strategy**: Automated dumps to GitHub + email

**Rationale:**
- Free tier available on Railway ($5 credit/month covers small usage)
- Streamlit Cloud works seamlessly with external PostgreSQL
- True persistence (no data loss on reboot)
- Can still export to SQLite for offline analysis

---

## 📁 New Folder Structure

```
sbv-pipeline/
├── src/
│   ├── drivers/                     # NEW: Data source drivers
│   │   ├── __init__.py
│   │   ├── base.py                  # Base driver interface
│   │   ├── progress.py              # Progress tracking utilities
│   │   ├── tavily/
│   │   │   ├── __init__.py
│   │   │   ├── driver.py
│   │   │   ├── parser.py            # Parse Tavily responses
│   │   │   └── README.md
│   │   ├── wayback/
│   │   │   ├── __init__.py
│   │   │   ├── driver.py
│   │   │   ├── parser.py
│   │   │   └── README.md
│   │   ├── crunchbase/
│   │   │   ├── __init__.py
│   │   │   ├── driver.py
│   │   │   ├── parser.py
│   │   │   └── README.md
│   │   ├── serpapi/
│   │   │   ├── __init__.py
│   │   │   ├── driver.py
│   │   │   └── README.md
│   │   ├── web_scraper/             # Existing scraper refactored
│   │   │   ├── __init__.py
│   │   │   ├── driver.py
│   │   │   └── README.md
│   │   └── manager.py               # Orchestrates all drivers
│   ├── storage/
│   │   ├── models.py                # Add new models for source data
│   │   ├── source_repository.py     # NEW: CRUD for source data
│   │   └── source_config.py         # NEW: Source enable/disable state
│   └── dashboard/
│       └── components/
│           ├── source_config.py     # UI for toggling sources
│           └── progress_bars.py     # Real-time progress indicators
├── scripts/
│   ├── backup_db.py                 # Automated backup script
│   ├── restore_db.py                # Restore from backup
│   ├── email_backup.py              # Email dump to user
│   ├── local_setup.sh               # Set up local PostgreSQL
│   └── test_local.sh                # Run full local test
├── .env.example                     # Template with all new API keys
├── .streamlit/
│   └── secrets.toml.example         # Streamlit Cloud secrets template
└── docker-compose.yml               # Local PostgreSQL + app
```

---

## 🗄️ Database Schema Extensions

### New Tables:

```sql
-- Store data from each source independently
CREATE TABLE source_runs (
    id UUID PRIMARY KEY,
    company_id INT REFERENCES companies(id),
    source_name VARCHAR(50),  -- 'tavily', 'wayback', 'crunchbase', etc.
    status VARCHAR(20),        -- 'pending', 'running', 'completed', 'failed'
    progress_percent FLOAT,    -- 0-100
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    raw_data JSONB,            -- Store full API response
    created_at TIMESTAMP DEFAULT NOW()
);

-- Source configuration (enable/disable per user)
CREATE TABLE source_config (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(50) UNIQUE,
    is_enabled BOOLEAN DEFAULT TRUE,
    priority INT DEFAULT 10,
    last_modified TIMESTAMP DEFAULT NOW()
);

-- Extracted structured data from each source
CREATE TABLE source_data (
    id SERIAL PRIMARY KEY,
    source_run_id UUID REFERENCES source_runs(id),
    company_id INT REFERENCES companies(id),
    data_type VARCHAR(50),     -- 'funding', 'employee_count', 'news', etc.
    data_value JSONB,
    confidence_score FLOAT,    -- How confident is this data?
    created_at TIMESTAMP DEFAULT NOW()
);

-- Backup logs
CREATE TABLE backup_logs (
    id SERIAL PRIMARY KEY,
    backup_type VARCHAR(20),   -- 'email', 'github', 's3'
    file_size BIGINT,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔧 Environment Configuration

### `.env` (Local Development)
```bash
# Database (Local: SQLite, Cloud: PostgreSQL)
DATABASE_URL=postgresql://user:pass@localhost:5432/sbv_db
# Or for local testing:
# DATABASE_URL=sqlite:///data/sbv.db

# LLM APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Data Source APIs
TAVILY_API_KEY=tvly-...
CRUNCHBASE_API_KEY=...
SERPAPI_KEY=...
WAYBACK_API_KEY=  # (No key needed, it's free)

# Email (for backups)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=alonof27@gmail.com
SMTP_PASSWORD=your-app-specific-password
BACKUP_EMAIL=alonof27@gmail.com

# GitHub (for DB backups)
GITHUB_TOKEN=ghp_...
GITHUB_REPO=Alon2303/SBV-ANALYSIS
GITHUB_BACKUP_PATH=backups/

# Source Toggles (default states)
ENABLE_TAVILY=true
ENABLE_WAYBACK=true
ENABLE_CRUNCHBASE=true
ENABLE_SERPAPI=false
ENABLE_WEB_SCRAPER=true
```

### `.streamlit/secrets.toml` (Streamlit Cloud)
```toml
# Database (External PostgreSQL)
DATABASE_URL = "postgresql://user:pass@region.railway.app:5432/railway"

# LLM APIs
OPENAI_API_KEY = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."

# Data Source APIs
TAVILY_API_KEY = "tvly-..."
CRUNCHBASE_API_KEY = "..."
SERPAPI_KEY = "..."

# Email
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "alonof27@gmail.com"
SMTP_PASSWORD = "your-app-password"
BACKUP_EMAIL = "alonof27@gmail.com"

# Source Toggles
ENABLE_TAVILY = true
ENABLE_WAYBACK = true
ENABLE_CRUNCHBASE = true
ENABLE_SERPAPI = false
ENABLE_WEB_SCRAPER = true
```

---

## 🚀 Implementation Steps (20 Steps)

### Phase 1: Infrastructure Setup (Steps 1-5)

#### Step 1: Database Migration to PostgreSQL
**What:** Update models and config to support PostgreSQL
**Files:**
- `src/storage/models.py` - Add new tables
- `src/config.py` - Support both SQLite and PostgreSQL
- `requirements.txt` - Add `psycopg2-binary` back
**Duration:** 2 hours

#### Step 2: Create Base Driver Interface
**What:** Abstract class all drivers inherit from
**Files:**
- `src/drivers/base.py`
- `src/drivers/progress.py`
**Key Features:**
- `run(company_name, **kwargs) -> Dict`
- `get_progress() -> float`
- `is_enabled() -> bool`
- Standardized error handling
**Duration:** 1 hour

#### Step 3: Create Driver Manager
**What:** Orchestrates parallel execution of all enabled drivers
**Files:**
- `src/drivers/manager.py`
**Key Features:**
- Loads config from DB
- Runs drivers in parallel (asyncio)
- Aggregates progress
- Merges results
**Duration:** 2 hours

#### Step 4: Source Configuration UI
**What:** Streamlit UI to toggle sources on/off
**Files:**
- `src/dashboard/components/source_config.py`
**Features:**
- Checkboxes for each source
- Priority sliders
- Save to database
**Duration:** 1 hour

#### Step 5: Progress Tracking UI
**What:** Real-time progress bars
**Files:**
- `src/dashboard/components/progress_bars.py`
**Features:**
- Per-source progress bars
- Overall progress
- Status indicators (✅❌⏳)
**Duration:** 1 hour

---

### Phase 2: Driver Implementation (Steps 6-10)

#### Step 6: Refactor Web Scraper as Driver
**What:** Move existing scraper to driver pattern
**Files:**
- `src/drivers/web_scraper/driver.py` (refactored from `src/research/web_scraper.py`)
**Duration:** 1 hour

#### Step 7: Implement Wayback Machine Driver (FREE)
**What:** Fetch historical snapshots
**Files:**
- `src/drivers/wayback/driver.py`
**API:** `https://archive.org/wayback/available?url=...`
**Data Extracted:**
- First snapshot date
- Latest snapshot date
- Company age
**Duration:** 2 hours

#### Step 8: Implement Tavily Driver (PAID - $30/month)
**What:** AI-powered web search
**Files:**
- `src/drivers/tavily/driver.py`
**API:** Tavily Search API
**Data Extracted:**
- Company mentions
- News articles
- Funding announcements
- Technical papers
**Duration:** 2 hours

#### Step 9: Implement Crunchbase Driver (FREE tier)
**What:** Startup database
**Files:**
- `src/drivers/crunchbase/driver.py`
**API:** Crunchbase API v4
**Data Extracted:**
- Funding rounds
- Investors
- Employee count
- Industry tags
**Duration:** 3 hours

#### Step 10: Implement SerpAPI Driver (PAID - $50/month)
**What:** Google Search results
**Files:**
- `src/drivers/serpapi/driver.py`
**API:** SerpAPI
**Data Extracted:**
- Search results
- News
- Related companies
**Duration:** 2 hours

---

### Phase 3: Backup & Restore (Steps 11-14)

#### Step 11: Database Backup Script
**What:** Dump PostgreSQL to .sql file
**Files:**
- `scripts/backup_db.py`
**Features:**
- `pg_dump` wrapper
- Compression (gzip)
- Timestamp naming
**Duration:** 1 hour

#### Step 12: Email Backup Script
**What:** Send backup to email
**Files:**
- `scripts/email_backup.py`
**Features:**
- SMTP integration
- Attachment support
- Retry logic
**Duration:** 1 hour

#### Step 13: Restore Script
**What:** Restore from .sql backup
**Files:**
- `scripts/restore_db.py`
**Features:**
- `psql` wrapper
- Verification checks
**Duration:** 1 hour

#### Step 14: Automated Backup Cron Job
**What:** Schedule daily backups
**Files:**
- `scripts/cron_backup.sh`
**Features:**
- Runs daily at 2 AM
- Keeps last 7 backups
- Emails on failure
**Duration:** 30 minutes

---

### Phase 4: Local Development Setup (Steps 15-17)

#### Step 15: Docker Compose for Local PostgreSQL
**What:** Easy local database setup
**Files:**
- `docker-compose.yml`
**Services:**
- PostgreSQL 15
- pgAdmin (DB management UI)
**Duration:** 1 hour

#### Step 16: Local Setup Script
**What:** One-command local environment
**Files:**
- `scripts/local_setup.sh`
**Steps:**
1. Start Docker PostgreSQL
2. Run migrations
3. Seed test data
4. Start dashboard
**Duration:** 1 hour

#### Step 17: Local Testing Script
**What:** Run full analysis locally
**Files:**
- `scripts/test_local.sh`
**Features:**
- Tests all drivers
- Verifies DB connections
- Runs sample analysis
**Duration:** 1 hour

---

### Phase 5: Integration & Testing (Steps 18-20)

#### Step 18: Update Researcher to Use Drivers
**What:** Integrate driver manager into research flow
**Files:**
- `src/research/researcher.py`
**Changes:**
- Call driver manager instead of direct scraping
- Merge results from all sources
**Duration:** 2 hours

#### Step 19: Update Dashboard for Multi-Source Display
**What:** Show data provenance per metric
**Files:**
- `src/dashboard/app.py`
**Features:**
- Tooltips showing data sources
- Source reliability indicators
- Data freshness timestamps
**Duration:** 2 hours

#### Step 20: Streamlit Cloud Deployment Guide
**What:** Complete deployment documentation
**Files:**
- `DEPLOYMENT.md`
**Covers:**
- Setting up Railway PostgreSQL
- Configuring Streamlit secrets
- GitHub Actions for backups
**Duration:** 1 hour

---

## 📦 Database Deployment Strategy

### For Streamlit Cloud:

**Option A: Railway (Recommended)**
1. Sign up at railway.app (free $5 credit/month)
2. Create PostgreSQL database
3. Copy connection string to Streamlit secrets
4. Database persists across reboots
5. Can backup to GitHub via GitHub Actions

**Option B: Supabase (Alternative)**
1. Sign up at supabase.com (free tier)
2. Create project
3. Use connection string in Streamlit secrets
4. Built-in backups

**Populating Database:**
```bash
# Method 1: From local SQLite (one-time migration)
python scripts/migrate_sqlite_to_postgres.py

# Method 2: From backup
psql $DATABASE_URL < backup.sql

# Method 3: Via GitHub Actions (automated)
# - Commit seed data to repo
# - GitHub Action runs on push
# - Restores to Railway DB
```

**GitHub Integration:**
- **Can't upload DB itself**, but can:
  1. Commit backup .sql files to repo
  2. Use GitHub Actions to restore on deploy
  3. Schedule daily backup commits

---

## ⏱️ Time Estimate

| Phase | Steps | Duration |
|-------|-------|----------|
| Phase 1: Infrastructure | 1-5 | 7 hours |
| Phase 2: Drivers | 6-10 | 10 hours |
| Phase 3: Backup/Restore | 11-14 | 3.5 hours |
| Phase 4: Local Setup | 15-17 | 3 hours |
| Phase 5: Integration | 18-20 | 5 hours |
| **TOTAL** | **20 steps** | **~28.5 hours** |

**Realistic Timeline:** 4-5 working days

---

## 💰 Cost Analysis

| Service | Free Tier | Paid | Recommended |
|---------|-----------|------|-------------|
| **Database (Railway)** | $5 credit/month | $5/month | ✅ Use free credit |
| **Tavily API** | 1,000 searches | $30/month (5k) | ✅ Start with free |
| **Crunchbase** | Basic data | $29/month | ✅ Use free tier |
| **SerpAPI** | 100 searches | $50/month | ⚠️ Optional |
| **Email (Gmail SMTP)** | FREE | FREE | ✅ FREE |
| **Wayback Machine** | FREE | FREE | ✅ FREE |
| **TOTAL** | **$0/month** | ~$109/month | **$0-35/month** |

**Recommendation:** Start with free tiers, only upgrade when hitting limits.

---

## 🔒 Security Considerations

1. **Never commit .env to GitHub**
   - Already in `.gitignore`
   - Use `.env.example` as template

2. **Streamlit Secrets are encrypted**
   - Safe to store API keys
   - Not visible in logs

3. **Database Credentials**
   - Use environment variables only
   - Rotate passwords regularly

4. **Email App Password**
   - Use Gmail App-Specific Password (not main password)
   - Enable 2FA on Gmail first

---

## ✅ Deployment Checklist

### Local Development:
- [ ] Install PostgreSQL via Docker
- [ ] Copy `.env.example` to `.env`
- [ ] Add all API keys to `.env`
- [ ] Run `scripts/local_setup.sh`
- [ ] Test with `scripts/test_local.sh`

### Streamlit Cloud:
- [ ] Sign up for Railway (PostgreSQL)
- [ ] Get Tavily API key (free tier)
- [ ] Get Crunchbase API key (free tier)
- [ ] Configure Gmail App Password
- [ ] Copy all secrets to Streamlit Cloud settings
- [ ] Push to GitHub
- [ ] Test backup script manually

---

## 🚨 Known Issues & Solutions

### Issue 1: Streamlit Cloud Reboot Clears Data
**Solution:** Use external PostgreSQL (Railway/Supabase)

### Issue 2: GitHub File Size Limit (100MB)
**Solution:** 
- Store backups in GitHub Releases (2GB limit)
- Or use external storage (S3, Dropbox)

### Issue 3: Email Sending Fails
**Solution:**
- Use SendGrid API (free tier: 100 emails/day)
- More reliable than SMTP

### Issue 4: API Rate Limits
**Solution:**
- Implement exponential backoff
- Cache results in database
- Respect rate limits per driver

---

## 📊 Success Metrics

After implementation:
- ✅ Each source can run independently
- ✅ Real-time progress bars show status
- ✅ UI toggle controls which sources run
- ✅ Settings persist in database
- ✅ Daily automated backups to email
- ✅ Can restore from backup
- ✅ Works locally with Docker
- ✅ Works on Streamlit Cloud with Railway
- ✅ No data loss on reboot

---

## 🎯 Next Steps

**Should we proceed with this plan?**

**I recommend:**
1. Start with **Phase 1** (Infrastructure) today
2. Implement **Wayback driver** (FREE, easy) tomorrow
3. Add **Tavily driver** (best ROI) day 3
4. Test full pipeline day 4
5. Deploy to Streamlit Cloud day 5

**Alternatively**, I can:
- Simplify plan (skip some drivers)
- Keep SQLite + manual backups (simpler)
- Focus on just Tavily + Wayback (most valuable)

**What would you like to do?**

