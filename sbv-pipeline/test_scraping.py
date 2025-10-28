"""Test script to diagnose scraping and analysis issues."""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.research.web_scraper import WebScraper, scrape_with_requests
from src.research.researcher import CompanyResearcher
from src.config import settings


async def test_playwright():
    """Test if Playwright is working."""
    print("=" * 60)
    print("Testing Playwright...")
    print("=" * 60)
    try:
        from playwright.async_api import async_playwright
        print("✓ Playwright module is installed")
        
        async with WebScraper() as scraper:
            print("✓ Playwright browser launched")
            
            # Test scraping
            url = "https://www.quantumscape.com/"
            print(f"\nScraping test URL: {url}")
            result = await scraper.scrape_url(url)
            
            if result["success"]:
                print(f"✓ Scraping successful!")
                print(f"  Title: {result['title']}")
                print(f"  Content length: {len(result['text_content'])} chars")
                print(f"  First 200 chars: {result['text_content'][:200]}...")
            else:
                print(f"✗ Scraping failed: {result['error']}")
                
    except ImportError as e:
        print(f"✗ Playwright not installed: {e}")
        print("\nRun: pip install playwright && python -m playwright install chromium")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True


async def test_fallback_scraping():
    """Test fallback scraping with requests."""
    print("\n" + "=" * 60)
    print("Testing Fallback Scraping (requests + BeautifulSoup)...")
    print("=" * 60)
    try:
        url = "https://www.quantumscape.com/"
        print(f"Scraping test URL: {url}")
        result = await asyncio.to_thread(scrape_with_requests, url)
        
        if result["success"]:
            print(f"✓ Fallback scraping successful!")
            print(f"  Title: {result['title']}")
            print(f"  Content length: {len(result['text_content'])} chars")
            print(f"  First 200 chars: {result['text_content'][:200]}...")
        else:
            print(f"✗ Fallback scraping failed: {result['error']}")
            
    except Exception as e:
        print(f"✗ Error: {e}")


async def test_full_research():
    """Test full research pipeline."""
    print("\n" + "=" * 60)
    print("Testing Full Research Pipeline...")
    print("=" * 60)
    
    # Check API key
    print(f"\nOpenAI API Key configured: {'Yes' if settings.openai_api_key and settings.openai_api_key != 'your-key-here' else 'NO - SET IN .env FILE!'}")
    
    if not settings.openai_api_key or settings.openai_api_key == "your-key-here":
        print("\n⚠️  Cannot test LLM without API key!")
        print("   Add OPENAI_API_KEY to your .env file to enable full testing")
        return
    
    researcher = CompanyResearcher()
    company_name = "QuantumScape"
    homepage = "https://www.quantumscape.com/"
    
    print(f"\nResearching: {company_name}")
    print(f"Homepage: {homepage}")
    
    try:
        result = await researcher.research_company(company_name, homepage)
        
        print(f"\n✓ Research completed!")
        print(f"  Homepage found: {result.get('homepage')}")
        print(f"  Scraped pages: {len(result.get('scraped_content', []))}")
        
        company_info = result.get("company_info", {})
        if "error" in company_info:
            print(f"  ✗ Company info extraction failed: {company_info['error']}")
        else:
            print(f"  Company description: {company_info.get('description', 'N/A')[:100]}...")
            print(f"  Technical claims: {len(company_info.get('technical_claims', []))} found")
            
        # Test bottleneck analysis
        print("\n  Testing bottleneck analysis...")
        bottlenecks = await researcher.analyze_bottlenecks(company_info, result)
        print(f"  Bottlenecks identified: {len(bottlenecks)}")
        if bottlenecks:
            for bn in bottlenecks[:3]:
                print(f"    - {bn.get('id', 'Unknown')}: {bn.get('location', 'N/A')} (severity: {bn.get('severity', 'N/A')})")
        
    except Exception as e:
        print(f"\n✗ Research failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    print("\n🔍 SBV Pipeline Diagnostic Tests\n")
    
    playwright_ok = await test_playwright()
    
    if not playwright_ok:
        await test_fallback_scraping()
    
    await test_full_research()
    
    print("\n" + "=" * 60)
    print("Diagnostic complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

