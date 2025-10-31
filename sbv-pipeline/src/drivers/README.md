# Data Source Drivers

This directory contains modular drivers for fetching company data from multiple sources.

## Available Drivers

### 1. **Wayback Machine** (FREE)
- **Path**: `wayback/driver.py`
- **API Key**: Not required
- **Cost**: FREE
- **Data**: Historical website snapshots, company age
- **Status**: ✅ Fully implemented

### 2. **Tavily AI Search** (PAID)
- **Path**: `tavily/driver.py`
- **API Key**: Required (`TAVILY_API_KEY`)
- **Cost**: $30/month (5,000 searches)
- **Data**: AI-powered web search, structured content
- **Status**: ✅ Fully implemented

### 3. **Crunchbase** (PAID)
- **Path**: `crunchbase/driver.py`
- **API Key**: Required (`CRUNCHBASE_API_KEY`)
- **Cost**: $29/month
- **Data**: Funding, investors, employee count
- **Status**: ✅ Fully implemented

### 4. **SerpAPI** (PAID)
- **Path**: `serpapi/driver.py`
- **API Key**: Required (`SERPAPI_KEY`)
- **Cost**: $50/month (5,000 searches)
- **Data**: Google Search results, news
- **Status**: ✅ Fully implemented

## Usage

### Quick Start

```python
from src.drivers import DriverManager
from src.config import settings

# Initialize manager with config from .env
manager = DriverManager(config=settings.get_driver_config())

# Run all enabled drivers in parallel
results = await manager.run_all(
    company_name="Intel Corp",
    homepage="https://www.intel.com"
)

# Access individual results
wayback_data = results["wayback"].data
tavily_data = results["tavily"].data
```

### Running a Single Driver

```python
# Run only Wayback Machine
result = await manager.run_single(
    driver_name="wayback",
    company_name="Intel Corp",
    homepage="https://www.intel.com"
)

print(f"Company age: {result.data['company_age_years']} years")
```

### Checking Driver Status

```python
# List all drivers
drivers = manager.list_drivers()
for driver in drivers:
    print(f"{driver['display_name']}: {driver['status']}")
    
# Get overall progress
progress = manager.get_aggregate_progress()
print(f"Overall progress: {progress}%")
```

## Configuration

Set these in your `.env` file:

```bash
# Enable/disable drivers
ENABLE_WAYBACK=true      # FREE - recommended
ENABLE_TAVILY=false      # Set to true when you have API key
ENABLE_CRUNCHBASE=false  # Set to true when you have API key
ENABLE_SERPAPI=false     # Set to true when you have API key

# API Keys (only needed if driver is enabled)
TAVILY_API_KEY=tvly-your-key
CRUNCHBASE_API_KEY=your-key
SERPAPI_KEY=your-key
```

## Architecture

```
drivers/
├── base.py                 # BaseDriver abstract class
├── manager.py              # DriverManager orchestrator
├── wayback/
│   └── driver.py          # WaybackDriver
├── tavily/
│   └── driver.py          # TavilyDriver
├── crunchbase/
│   └── driver.py          # CrunchbaseDriver
└── serpapi/
    └── driver.py          # SerpAPIDriver
```

## Adding a New Driver

1. Create a new directory: `drivers/newsource/`
2. Implement `NewsourceDriver(BaseDriver)`:
   ```python
   from ..base import BaseDriver
   
   class NewsourceDriver(BaseDriver):
       @property
       def name(self) -> str:
           return "newsource"
       
       @property
       def display_name(self) -> str:
           return "New Source"
       
       @property
       def description(self) -> str:
           return "Description of what this source provides"
       
       def requires_api_key(self) -> bool:
           return True  # or False
       
       async def _fetch_data(self, company_name, homepage=None, **kwargs):
           # Your data fetching logic here
           return {"key": "value"}
   ```

3. Register in `manager.py`:
   ```python
   from .newsource import NewsourceDriver
   
   # In _initialize_drivers():
   self.drivers["newsource"] = NewsourceDriver(
       api_key=config.get("newsource", {}).get("api_key"),
       is_enabled=config.get("newsource", {}).get("enabled", False)
   )
   ```

## Testing

```bash
# Test a single driver
cd sbv-pipeline
python -c "
import asyncio
from src.drivers.wayback import WaybackDriver

async def test():
    driver = WaybackDriver()
    result = await driver.run('Intel Corp', 'https://www.intel.com')
    print(result.data)

asyncio.run(test())
"
```

## Features

- ✅ **Parallel Execution**: All drivers run simultaneously
- ✅ **Progress Tracking**: Real-time progress (0-100%) per driver
- ✅ **Graceful Degradation**: If one driver fails, others continue
- ✅ **Enable/Disable**: Toggle drivers on/off via config
- ✅ **API Key Management**: Automatic detection of missing keys
- ✅ **Retry Logic**: Built-in retry with exponential backoff
- ✅ **Timeout Handling**: Configurable timeouts per driver
- ✅ **Result Aggregation**: Combine data from all sources

## Status Codes

- `IDLE`: Driver not started
- `RUNNING`: Currently fetching data
- `COMPLETED`: Successfully finished
- `FAILED`: Error occurred
- `DISABLED`: Driver is disabled in config
- `MISSING_API_KEY`: API key required but not provided

