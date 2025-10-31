# 🎯 Next Steps: Modular Data Sources Implementation

## ✅ What I've Created for You

I've prepared a complete implementation plan and starter files. Here's what's ready:

### 📄 Documentation
1. **`MODULAR_SOURCES_PLAN.md`** - Complete 20-step implementation plan
   - Database strategy analysis (SQLite vs PostgreSQL vs MySQL)
   - Folder structure design
   - Step-by-step implementation guide
   - Cost analysis
   - Deployment strategy

### ⚙️ Configuration Files
2. **`sbv-pipeline/env.example`** - Environment variables template
   - All API keys needed (Tavily, Crunchbase, SerpAPI, etc.)
   - Email configuration for backups
   - Source enable/disable flags

3. **`.streamlit/secrets.toml.example`** - Streamlit Cloud secrets template
   - Copy-paste ready for Streamlit Cloud deployment

4. **`docker-compose.yml`** - Local PostgreSQL setup
   - PostgreSQL 15 database
   - pgAdmin (database management UI)
   - Redis (for caching)
   - One command: `docker-compose up -d`

### 🛠️ Scripts
5. **`scripts/backup_db.py`** - Database backup script
   - Works with both SQLite and PostgreSQL
   - Compresses backups (gzip)
   - Can email backups to alonof27@gmail.com
   - Usage: `python scripts/backup_db.py --email`

6. **`scripts/restore_db.py`** - Database restore script
   - Restores from compressed backup
   - Safety confirmation before overwriting
   - Usage: `python scripts/restore_db.py backups/sbv_backup_YYYYMMDD.sql.gz`

7. **`scripts/local_setup.sh`** - One-command local setup
   - Starts Docker PostgreSQL
   - Creates Python venv
   - Installs dependencies
   - Initializes database
   - Verifies setup
   - Usage: `./scripts/local_setup.sh`

---

## 🚨 CRITICAL DECISION NEEDED

Before we implement, **you need to decide on the database strategy:**

### Option 1: SQLite + GitHub ✅ SIMPLEST (Current)
**Pros:**
- ✅ FREE
- ✅ Already working
- ✅ Simple backup (just copy file)
- ✅ Good for < 100 companies

**Cons:**
- ❌ Streamlit Cloud resets data on reboot (need manual backup/restore)
- ❌ No concurrent writes
- ❌ Limited to ~100MB on GitHub

**Best for:** Testing, small-scale (<100 companies), budget-conscious

---

### Option 2: PostgreSQL + Railway ⭐ RECOMMENDED
**Pros:**
- ✅ $5/month (or free with $5 monthly credit)
- ✅ True persistence (survives Streamlit reboots)
- ✅ Concurrent writes
- ✅ Scalable to millions of records
- ✅ Professional grade

**Cons:**
- ❌ $5/month cost (free tier available)
- ❌ Requires external service setup

**Best for:** Production, scaling to 100+ companies, reliable deployment

**Setup Steps:**
1. Sign up at [railway.app](https://railway.app)
2. Create PostgreSQL database (1-click)
3. Copy connection string to `.streamlit/secrets.toml`
4. Done!

---

### Option 3: MySQL + PlanetScale/AWS
**Pros:**
- ✅ As requested by you
- ✅ Serverless options

**Cons:**
- ❌ $10-30/month
- ❌ More complex than PostgreSQL
- ❌ Less Streamlit Cloud documentation

**Best for:** If you specifically need MySQL for other reasons

---

## 💡 MY RECOMMENDATION

**Start with Option 2 (PostgreSQL + Railway)** because:

1. **Free tier available** - Railway gives $5 credit/month, which covers small usage
2. **True persistence** - No data loss on Streamlit Cloud reboots
3. **Industry standard** - PostgreSQL is more common in Python/Streamlit ecosystem
4. **Easy migration** - Can export to SQLite later if needed
5. **Better long-term** - Scales as you add more companies

**You can test locally with SQLite first** using the existing setup, then migrate to PostgreSQL when ready for production.

---

## 🗓️ Implementation Timeline (If You Approve)

### Week 1: Infrastructure (7 hours)
- [ ] Migrate to PostgreSQL (or keep SQLite - your choice)
- [ ] Create base driver interface
- [ ] Create driver manager for parallel execution
- [ ] Build UI for source toggles
- [ ] Build progress bars

### Week 2: Data Source Drivers (10 hours)
- [ ] Refactor web scraper to driver pattern
- [ ] Implement Wayback Machine driver (FREE)
- [ ] Implement Tavily driver ($30/month)
- [ ] Implement Crunchbase driver (FREE tier)
- [ ] Optionally add SerpAPI ($50/month)

### Week 3: Testing & Deployment (5 hours)
- [ ] Test locally with Docker
- [ ] Test backup/restore scripts
- [ ] Deploy to Streamlit Cloud
- [ ] Verify all sources work
- [ ] Documentation

**Total:** ~22-28 hours of work (3-4 working days)

---

## 🎬 Quick Start Options

### Option A: Test Locally Right Now
```bash
# 1. Set up local environment
./scripts/local_setup.sh

# 2. Access pgAdmin (database UI)
# Open: http://localhost:5050
# Email: alonof27@gmail.com, Password: admin

# 3. Run dashboard
cd sbv-pipeline
streamlit run src/dashboard/app.py

# 4. Create backup
cd ..
python scripts/backup_db.py --email
```

### Option B: Keep Current Setup (SQLite)
Continue using SQLite, add manual backup routine:
```bash
# Create backup before Streamlit Cloud deploy
python scripts/backup_db.py --email

# After Streamlit Cloud reboot, restore:
python scripts/restore_db.py backups/latest_backup.sql.gz
```

### Option C: Migrate to PostgreSQL (Railway)
1. Sign up at railway.app
2. Create PostgreSQL database
3. Update `.env`:
   ```bash
   DATABASE_URL=postgresql://postgres:pass@region.railway.app:5432/railway
   ```
4. Run migrations:
   ```bash
   cd sbv-pipeline
   python -c "from src.storage.database import init_db; init_db()"
   ```
5. Deploy to Streamlit Cloud with new `DATABASE_URL` in secrets

---

## 📋 To-Do Before Implementation

Please confirm:

1. **Database choice:**
   - [ ] Keep SQLite (simple, free, manual backups)
   - [ ] Migrate to PostgreSQL on Railway ($5/month, persistent)
   - [ ] Use MySQL on PlanetScale ($10+/month)

2. **Which data sources to implement first?** (Priority order)
   - [ ] Wayback Machine (FREE, easy, 2 hours)
   - [ ] Tavily API ($30/month, most valuable, 2 hours)
   - [ ] Crunchbase (FREE tier, 3 hours)
   - [ ] SerpAPI ($50/month, optional, 2 hours)
   - [ ] LinkedIn/Patent data (future)

3. **Budget approval:**
   - [ ] Approved for Tavily API ($30/month)?
   - [ ] Approved for Railway PostgreSQL ($5/month)?
   - [ ] Approved for SerpAPI ($50/month)?
   - [ ] Stick to free sources only?

4. **Deployment preference:**
   - [ ] Deploy to Streamlit Cloud with persistent database
   - [ ] Keep local only for now
   - [ ] Deploy to other platform (Heroku, AWS, etc.)

---

## 🚀 Ready to Start?

Once you confirm the above decisions, I'll:

1. ✅ Implement the base driver system (already planned)
2. ✅ Add progress tracking UI (already designed)
3. ✅ Implement your chosen data sources
4. ✅ Set up backup automation
5. ✅ Deploy to production

**Just tell me:**
- Which database option (SQLite/PostgreSQL/MySQL)?
- Which data sources to add first?
- What's your budget for APIs?

Then I'll start implementing immediately! 🚀

---

## 📧 Questions?

Ask me anything about:
- Database trade-offs
- API costs vs. value
- Implementation complexity
- Deployment strategies
- Data source capabilities

I'm ready to proceed when you are! 💪

