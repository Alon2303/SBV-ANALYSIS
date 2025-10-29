"""Web scraping utilities."""
import asyncio
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class WebScraper:
    """Web scraper using Playwright."""
    
    def __init__(self):
        self.browser = None
        self.playwright = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        from playwright.async_api import async_playwright
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def scrape_url(self, url: str, timeout: int = 30000) -> Dict[str, Any]:
        """
        Scrape a URL and return content.
        
        Args:
            url: URL to scrape
            timeout: Timeout in milliseconds
        
        Returns:
            Dict with url, title, text_content, html
        """
        try:
            page = await self.browser.new_page()
            await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            
            # Wait a bit for dynamic content
            await page.wait_for_timeout(2000)
            
            title = await page.title()
            html = await page.content()
            
            # Extract text content
            text_content = await page.evaluate("""
                () => {
                    // Remove script and style elements
                    const scripts = document.querySelectorAll('script, style, nav, footer');
                    scripts.forEach(el => el.remove());
                    
                    // Get main content
                    const main = document.querySelector('main') || document.body;
                    return main.innerText;
                }
            """)
            
            await page.close()
            
            return {
                "url": url,
                "title": title,
                "text_content": text_content[:50000],  # Limit size
                "html": html[:100000],  # Limit size
                "success": True,
                "error": None
            }
        
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {
                "url": url,
                "title": None,
                "text_content": None,
                "html": None,
                "success": False,
                "error": str(e)
            }
    
    async def scrape_multiple(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape multiple URLs concurrently."""
        tasks = [self.scrape_url(url) for url in urls]
        return await asyncio.gather(*tasks)


def scrape_with_requests(url: str) -> Dict[str, Any]:
    """
    Simple scraping with requests (fallback).
    
    Args:
        url: URL to scrape
    
    Returns:
        Dict with url, text_content
    """
    import requests
    from bs4 import BeautifulSoup
    import time
    
    # More complete headers to look like a real browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0"
    }
    
    # Try with retries
    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url, 
                timeout=15, 
                headers=headers,
                allow_redirects=True
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()
            
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            text_content = '\n'.join(line for line in lines if line)
            
            return {
                "url": url,
                "title": soup.title.string if soup.title else None,
                "text_content": text_content[:50000],
                "success": True,
                "error": None
            }
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                error_msg = f"403 Forbidden - {url} is blocking automated access. This site requires Playwright (browser automation) to scrape."
                logger.warning(error_msg)
                return {
                    "url": url,
                    "text_content": None,
                    "success": False,
                    "error": error_msg,
                    "needs_playwright": True
                }
            elif attempt < max_retries - 1:
                time.sleep(2)  # Wait before retry
                continue
            else:
                logger.error(f"HTTP error scraping {url}: {str(e)}")
                return {
                    "url": url,
                    "text_content": None,
                    "success": False,
                    "error": str(e)
                }
        
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait before retry
                continue
            else:
                logger.error(f"Error scraping {url} with requests: {str(e)}")
                return {
                    "url": url,
                    "text_content": None,
                    "success": False,
                    "error": str(e)
                }
    
    # Should never reach here, but just in case
    return {
        "url": url,
        "text_content": None,
        "success": False,
        "error": "Max retries exceeded"
    }

