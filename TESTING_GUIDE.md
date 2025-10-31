# 🧪 Testing Guide - Data Source Drivers

## Quick Test (5 minutes)

### Test 1: Wayback Machine (FREE - No API Key Needed)

```bash
cd /Users/alonofir/Documents/P
python test_drivers.py
```

**What this tests:**
- ✅ Driver initialization
- ✅ Configuration loading
- ✅ Wayback Machine API integration
- ✅ Progress tracking
- ✅ Error handling
- ✅ Results formatting

**Expected Output:**
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
      • View oldest: https://web.archive.org/web/...
   ⏱️  Duration: 2.34s
```

---

### Test 2: All Enabled Drivers (Parallel)

```bash
python test_drivers.py --all
```

**What this tests:**
- ✅ Parallel execution of multiple drivers
- ✅ Aggregate progress calculation
- ✅ Graceful degradation (if one fails, others continue)

---

## Adding API Keys (Optional)

To test paid sources, add API keys to your `.env` file:

### Step 1: Copy template

```bash
cd sbv-pipeline
cp env.example ../.env
```

### Step 2: Edit `.env` and add keys

```bash
# Enable and add API keys
ENABLE_TAVILY=true
TAVILY_API_KEY=tvly-your-actual-key-here

ENABLE_CRUNCHBASE=true
CRUNCHBASE_API_KEY=your-actual-key-here

ENABLE_SERPAPI=true
SERPAPI_KEY=your-actual-key-here
```

### Step 3: Get free API keys

**Tavily** (1,000 searches/month free):
1. Sign up: https://app.tavily.com/sign-up
2. Copy API key from dashboard
3. Paste into `.env`

**Crunchbase** (Basic tier free):
1. Sign up: https://www.crunchbase.com/
2. Go to API settings
3. Copy key to `.env`

**SerpAPI** (100 searches/month free):
1. Sign up: https://serpapi.com/users/sign_up
2. Copy API key
3. Paste into `.env`

### Step 4: Test with API keys

```bash
python test_drivers.py --all
```

Now you'll see all 4 sources working!

---

## Troubleshooting

### Issue: "No module named 'src'"

**Solution:**
```bash
cd /Users/alonofir/Documents/P
python test_drivers.py  # Run from project root
```

### Issue: "requests module not found"

**Solution:**
```bash
cd sbv-pipeline
pip install requests
```

### Issue: "Wayback Machine timeout"

**Solution:** The API might be slow. This is normal, just wait or retry.

### Issue: "API key invalid"

**Solution:** Double-check:
1. API key has no extra spaces
2. API key is in `.env` file at project root
3. Correct variable name (e.g., `TAVILY_API_KEY` not `TAVILY_KEY`)

---

## What to Look For

### ✅ **Good Signs:**

1. **Wayback Machine returns data:**
   - Company age in years
   - Number of snapshots
   - First/latest snapshot dates
   - URLs to view archived versions

2. **Progress tracking works:**
   - Progress goes from 0% → 100%
   - Duration is measured

3. **Parallel execution works:**
   - Multiple sources run simultaneously
   - Results come back at different times
   - Aggregate progress updates

### ⚠️ **Expected Warnings:**

1. **Missing API keys:**
   ```
   ⏸️ Tavily AI Search: missing_api_key 🔑
   ```
   **This is normal** - just add API key when ready

2. **Some companies not in archive:**
   ```
   • Available in archive: False
   • Message: The website has not been archived
   ```
   **This is normal** - very new companies might not be archived yet

3. **Timeout for slow APIs:**
   ```
   ❌ Failed: Timeout after 60s
   ```
   **Increase timeout** in driver config if needed

---

## Performance Benchmarks

Expected response times:

| Driver | First Call | Cached | Notes |
|--------|-----------|--------|-------|
| **Wayback** | 2-5s | 1-2s | Sometimes slow, normal |
| **Tavily** | 3-8s | - | Depends on search depth |
| **Crunchbase** | 1-3s | - | Usually fast |
| **SerpAPI** | 2-4s | - | Google Search latency |

**Parallel execution** (all 4): ~8-10s (max of slowest driver)

---

## Next Steps After Testing

Once you've verified the drivers work:

1. **I'll implement:**
   - ✅ UI toggles for enabling/disabling sources
   - ✅ Real-time progress bars in dashboard
   - ✅ Integration with existing researcher
   - ✅ Database models for source tracking

2. **You'll have:**
   - Full control over which sources to use
   - Real-time progress visibility
   - Data from all sources combined
   - Persistent source configuration

---

## Questions?

If you encounter any issues:

1. Check the error message (usually very descriptive)
2. Verify API keys are correct
3. Check internet connection
4. Try running with just Wayback first (no API key needed)

**Ready to continue with UI implementation once testing is complete!** 🚀

