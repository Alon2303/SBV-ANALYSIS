# SBV Pipeline Diagnosis: Why CI = 0.000

## Problem Summary

All analyses show `CI = 0.000` because **no bottlenecks are being identified** during the research phase.

## Root Causes

### 1. **Web Scraping Not Working** 
- Playwright may not be properly installed
- Chromium browser may not be downloaded
- Websites may be blocking requests

### 2. **LLM Analysis Not Working**
- OpenAI API key not configured
- API key invalid or rate limited
- LLM not returning structured bottleneck data

## How to Diagnose

### Check 1: Verify Playwright Installation

```bash
cd /Users/alonofir/Documents/P/sbv-pipeline
python3 -c "from playwright.async_api import async_playwright; print('✓ Playwright is installed')"
python3 -m playwright install chromium
```

### Check 2: Verify API Key

```bash
cd /Users/alonofir/Documents/P/sbv-pipeline
python3 -c "from src.config import settings; print(f'API Key: {settings.openai_api_key[:10]}...' if settings.openai_api_key and settings.openai_api_key != 'your-key-here' else 'NOT CONFIGURED!')"
```

### Check 3: Run Analysis with Debugging

```bash
cd /Users/alonofir/Documents/P/sbv-pipeline
# Increase logging
export LOG_LEVEL=DEBUG
python3 -m src.main analyze data/input/example_companies.csv
```

Look for these log messages:
- `"Error scraping {url}:"` → Web scraping failed
- `"No content could be scraped"` → No text extracted from pages
- `"Error analyzing bottlenecks:"` → LLM analysis failed

## Quick Fix Options

### Option 1: Install Missing Dependencies (Recommended)

```bash
cd /Users/alonofir/Documents/P/sbv-pipeline

# If you have Python 3.13, install Python 3.11/3.12 first
# brew install python@3.11

# Use the correct Python version
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements-minimal.txt
python -m playwright install chromium

# Make sure .env has your API key
echo "OPENAI_API_KEY=sk-..." >> .env

# Run analysis again
python -m src.main analyze data/input/example_companies.csv
```

### Option 2: Use Streamlit Dashboard Upload Feature

The new dashboard UI allows you to:
1. Upload a CSV
2. Enter companies manually
3. Run analysis directly in the browser

The API key is read from Streamlit Cloud secrets (if deployed) or local `.env`.

### Option 3: Manual Test of One Company

Create a simple test:

```bash
cd /Users/alonofir/Documents/P/sbv-pipeline
python3 << 'EOF'
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from src.research import CompanyResearcher

async def test():
    researcher = CompanyResearcher()
    result = await researcher.research_company(
        "QuantumScape", 
        "https://www.quantumscape.com/"
    )
    
    print(f"Scraped pages: {len(result.get('scraped_content', []))}")
    print(f"Company info: {result.get('company_info', {}).keys()}")
    
    company_info = result.get("company_info", {})
    if "error" in company_info:
        print(f"ERROR: {company_info['error']}")
    else:
        print(f"Description: {company_info.get('description', 'N/A')[:100]}")
        
        # Test bottleneck analysis
        bottlenecks = await researcher.analyze_bottlenecks(company_info, result)
        print(f"\nBottlenecks found: {len(bottlenecks)}")
        for bn in bottlenecks:
            print(f"  - {bn.get('id')}: {bn.get('location')} (severity: {bn.get('severity')})")

asyncio.run(test())
EOF
```

## Expected Results

When working correctly, you should see:

✓ Scraped pages: 1-3  
✓ Company description extracted  
✓ Bottlenecks found: 3-7  
✓ CI > 0.3 (typically 0.4-0.8)  

If scraping works but bottlenecks are still 0:
- Check that OpenAI API key is valid
- Check API rate limits / billing
- Look at LLM response logs

## Why URLs Alone Aren't Enough

Yes, **adding homepage URLs is necessary**, but it's not sufficient:

1. URLs → **Web Scraper** → Extracts text content
2. Text content → **LLM** → Identifies bottlenecks
3. Bottlenecks → **CI Calculation** → Non-zero score

All three steps must work for CI to be meaningful.

## Next Steps

1. Run the checks above to identify which component is failing
2. Install missing dependencies
3. Verify API key is configured
4. Re-run analysis on 1-2 companies to test
5. Check that `k > 0` and `CI > 0` in results

If issues persist, check:
- API key billing/limits
- Network/firewall blocking requests
- Python environment activation

