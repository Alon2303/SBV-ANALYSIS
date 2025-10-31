"""SerpAPI Google Search driver."""
import asyncio
import logging
from typing import Dict, Any, Optional, List

import requests

from ..base import BaseDriver

logger = logging.getLogger(__name__)


class SerpAPIDriver(BaseDriver):
    """
    Driver for SerpAPI (Google Search).
    
    SerpAPI provides access to Google Search results via API:
    - Organic search results
    - News results
    - Related searches
    - Knowledge Graph data
    - Rich snippets
    
    Pricing:
    - Free: 100 searches/month
    - Pro: $50/month for 5,000 searches
    
    Docs: https://serpapi.com/docs
    """
    
    API_ENDPOINT = "https://serpapi.com/search"
    
    @property
    def name(self) -> str:
        return "serpapi"
    
    @property
    def display_name(self) -> str:
        return "SerpAPI (Google Search)"
    
    @property
    def description(self) -> str:
        return "Google Search results API ($50/month, 5k searches)"
    
    def requires_api_key(self) -> bool:
        return True
    
    async def _fetch_data(
        self,
        company_name: str,
        homepage: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch company information using Google Search via SerpAPI.
        
        Args:
            company_name: Name of the company
            homepage: Optional homepage URL
        
        Returns:
            Dictionary with search results
        """
        self.set_progress(10.0)
        
        # Construct search queries
        queries = [
            f"{company_name} company",
            f"{company_name} funding news",
            f"{company_name} technology innovation"
        ]
        
        all_results = []
        
        for i, query in enumerate(queries):
            progress = 10.0 + (i / len(queries)) * 80.0
            self.set_progress(progress)
            
            logger.info(f"SerpAPI search: '{query}'")
            
            try:
                result = await asyncio.to_thread(
                    self._search,
                    query
                )
                all_results.append({
                    "query": query,
                    "organic_results": result.get("organic_results", []),
                    "news_results": result.get("news_results", []),
                    "knowledge_graph": result.get("knowledge_graph", {}),
                    "related_searches": result.get("related_searches", [])
                })
            except Exception as e:
                logger.warning(f"SerpAPI search failed for '{query}': {e}")
                all_results.append({
                    "query": query,
                    "error": str(e)
                })
        
        # Structure results
        combined = {
            "company_name": company_name,
            "homepage": homepage,
            "searches": all_results,
            "knowledge_graph": all_results[0].get("knowledge_graph", {}) if all_results else {},
            "top_results": self._extract_top_results(all_results),
            "news": self._extract_news(all_results),
            "total_results": sum(len(r.get("organic_results", [])) for r in all_results)
        }
        
        self.set_progress(95.0)
        
        logger.info(
            f"✅ SerpAPI: Found {combined['total_results']} results "
            f"for '{company_name}'"
        )
        
        return combined
    
    def _search(
        self,
        query: str,
        num_results: int = 10
    ) -> Dict[str, Any]:
        """
        Execute a Google search via SerpAPI.
        
        Args:
            query: Search query
            num_results: Number of results to return
        
        Returns:
            Search results
        """
        params = {
            "api_key": self.api_key,
            "q": query,
            "num": num_results,
            "engine": "google",
            "gl": "us",  # Country (US)
            "hl": "en"   # Language (English)
        }
        
        response = requests.get(
            self.API_ENDPOINT,
            params=params,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        return response.json()
    
    def _extract_top_results(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract top organic results from all searches."""
        results = []
        seen_urls = set()
        
        for search in search_results:
            for result in search.get("organic_results", [])[:5]:  # Top 5 from each search
                link = result.get("link")
                if link and link not in seen_urls:
                    seen_urls.add(link)
                    results.append({
                        "title": result.get("title", ""),
                        "link": link,
                        "snippet": result.get("snippet", ""),
                        "position": result.get("position", 0),
                        "query": search.get("query", "")
                    })
        
        # Sort by position (lower is better)
        results.sort(key=lambda x: x.get("position", 999))
        
        return results[:20]  # Return top 20 overall
    
    def _extract_news(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract news results."""
        news = []
        seen_titles = set()
        
        for search in search_results:
            for item in search.get("news_results", []):
                title = item.get("title")
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    news.append({
                        "title": title,
                        "link": item.get("link", ""),
                        "source": item.get("source", ""),
                        "date": item.get("date", ""),
                        "snippet": item.get("snippet", "")
                    })
        
        return news

