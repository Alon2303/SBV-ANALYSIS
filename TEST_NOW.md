# 🚀 Test the Data Source Drivers - Quick Start

## Step-by-Step Testing Instructions

### Step 1: Install Dependencies (2 minutes)

```bash
cd /Users/alonofir/Documents/P/sbv-pipeline

# Activate virtual environment (if you have one)
source ../venv/bin/activate

# OR create a new one
python3 -m venv ../venv
source ../venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### Step 2: Run the Test (30 seconds)

```bash
cd /Users/alonofir/Documents/P
python3 test_drivers.py
```

**This will test:**
- ✅ Wayback Machine (FREE, no API key)
- Shows which drivers are available
- Tests on 3 companies: Intel, Tesla, OpenAI

---

### Expected Output:

```
🧪 Testing Wayback Machine Driver (FREE)
======================================================================

📋 Available Drivers:
   ✅ Wayback Machine: idle
   ⏸️ Tavily AI Search: missing_api_key 🔑
   ⏸️ Crunchbase: missing_api_key 🔑
   ⏸️ SerpAPI (Google Search): missing_api_key 🔑

🔍 Analyzing: Intel Corp
   Homepage: https://www.intel.com

   ✅ Success!
   📊 Results:
      • Available in archive: True
      • Total snapshots: 100
      • Company age: 27.3 years
      • First snapshot: 1997-06-03
      • Latest snapshot: 2024-10-30
      • View oldest: https://web.archive.org/web/19970603/http://www.intel.com
   ⏱️  Duration: 2.34s

🔍 Analyzing: Tesla
   ...

🔍 Analyzing: OpenAI
   ...

======================================================================
✅ Test Complete!
======================================================================
```

---

### Step 3 (Optional): Test with All Drivers

If you want to test parallel execution (even without API keys):

```bash
python3 test_drivers.py --all
```

This will show how all drivers run simultaneously.

---

## What You're Testing

✅ **Infrastructure:**
- Driver initialization
- Configuration loading from .env
- Progress tracking system
- Error handling

✅ **Wayback Machine Driver:**
- API integration
- Historical snapshot retrieval
- Company age calculation
- Data parsing

✅ **System Architecture:**
- Parallel execution capability
- Graceful degradation (drivers work independently)
- Result aggregation

---

## If You Get Errors

### Error: `ModuleNotFoundError: No module named 'pydantic_settings'`

**Solution:**
```bash
cd sbv-pipeline
pip install -r requirements.txt
```

### Error: `No module named 'requests'`

**Solution:**
```bash
pip install requests
```

### Error: `Wayback Machine timeout`

**This is normal** - Internet Archive can be slow. The driver has retry logic. Just wait or run again.

### Error: `Company not found in archive`

**This is normal** - Very new companies (< 1 year old) might not be archived yet.

---

## Next Steps

### ✅ After successful test:

Tell me the results and I'll immediately implement:

1. **UI Components** (2-3 hours):
   - Source toggle switches in dashboard
   - Real-time progress bars
   - Status indicators per source

2. **Integration** (1-2 hours):
   - Connect drivers to researcher
   - Merge multi-source data
   - Update analysis display

3. **Database Models** (1 hour):
   - Track source usage per analysis
   - Store raw data from each source
   - Query which sources were used

4. **Polish & Deploy** (1 hour):
   - Test end-to-end
   - Deploy to Streamlit Cloud
   - Verify all sources work

---

## Quick Reference

```bash
# Basic test (Wayback only)
python3 test_drivers.py

# Test all drivers (parallel)
python3 test_drivers.py --all

# Check driver status
python3 -c "
from sbv-pipeline.src.config import settings
from sbv-pipeline.src.drivers import DriverManager
manager = DriverManager(config=settings.get_driver_config())
for d in manager.list_drivers():
    print(f'{d[\"display_name\"]}: {d[\"status\"]}')
"
```

---

## What Success Looks Like

✅ **Green checkmarks** for Wayback Machine
✅ **Company age data** appears
✅ **Snapshot URLs** are provided
✅ **No crashes or errors**
⏸️ **Other drivers show "missing_api_key"** (this is expected)

---

**Once you've run the test and see it working, just say "Continue" and I'll immediately implement the UI components and integration!** 🚀

