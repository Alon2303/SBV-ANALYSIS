"""Tavily AI-powered search driver."""
import asyncio
import logging
from typing import Dict, Any, Optional, List

import requests

from ..base import BaseDriver

logger = logging.getLogger(__name__)


class TavilyDriver(BaseDriver):
    """
    Driver for Tavily AI Search API.
    
    Tavily is an AI-powered search engine designed for LLM applications.
    It returns cleaned, structured data perfect for research.
    
    Features:
    - AI-powered relevance ranking
    - Cleaned and structured content
    - Avoids bot-blocking issues
    - Returns citations and source URLs
    
    Pricing:
    - Free: 1,000 searches/month
    - Pro: $30/month for 5,000 searches
    
    Docs: https://docs.tavily.com/
    """
    
    API_ENDPOINT = "https://api.tavily.com/search"
    
    @property
    def name(self) -> str:
        return "tavily"
    
    @property
    def display_name(self) -> str:
        return "Tavily AI Search"
    
    @property
    def description(self) -> str:
        return "AI-powered web search ($30/month, 5k searches)"
    
    def requires_api_key(self) -> bool:
        return True
    
    async def _fetch_data(
        self,
        company_name: str,
        homepage: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch company information using Tavily AI Search.
        
        Args:
            company_name: Name of the company
            homepage: Optional homepage URL
        
        Returns:
            Dictionary with search results
        """
        self.set_progress(10.0)
        
        # Construct search queries
        queries = [
            f"{company_name} company technology",
            f"{company_name} funding investors",
            f"{company_name} technical specifications claims"
        ]
        
        all_results = []
        
        for i, query in enumerate(queries):
            progress = 10.0 + (i / len(queries)) * 80.0
            self.set_progress(progress)
            
            logger.info(f"Tavily search: '{query}'")
            
            try:
                result = await asyncio.to_thread(
                    self._search,
                    query
                )
                all_results.append({
                    "query": query,
                    "results": result.get("results", []),
                    "answer": result.get("answer", ""),
                })
            except Exception as e:
                logger.warning(f"Tavily search failed for '{query}': {e}")
                all_results.append({
                    "query": query,
                    "error": str(e),
                    "results": []
                })
        
        # Combine and structure results
        combined_results = {
            "company_name": company_name,
            "homepage": homepage,
            "searches": all_results,
            "total_sources": sum(len(r.get("results", [])) for r in all_results),
            "sources": self._extract_sources(all_results),
            "key_findings": self._extract_key_findings(all_results)
        }
        
        self.set_progress(95.0)
        
        logger.info(
            f"✅ Tavily: Found {combined_results['total_sources']} sources "
            f"for '{company_name}'"
        )
        
        return combined_results
    
    def _search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Execute a Tavily search.
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
        Returns:
            Search results
        """
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",  # or "basic"
            "include_answer": True,       # Get AI-generated answer
            "include_raw_content": False, # Don't need full HTML
            "max_results": max_results
        }
        
        response = requests.post(
            self.API_ENDPOINT,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        return response.json()
    
    def _extract_sources(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract unique sources from all search results."""
        sources = []
        seen_urls = set()
        
        for search in search_results:
            for result in search.get("results", []):
                url = result.get("url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    sources.append({
                        "title": result.get("title", ""),
                        "url": url,
                        "content": result.get("content", "")[:500],  # First 500 chars
                        "score": result.get("score", 0),
                        "query": search.get("query", "")
                    })
        
        # Sort by relevance score
        sources.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return sources
    
    def _extract_key_findings(self, search_results: List[Dict[str, Any]]) -> List[str]:
        """Extract key findings from AI-generated answers."""
        findings = []
        
        for search in search_results:
            answer = search.get("answer", "")
            if answer:
                findings.append({
                    "query": search.get("query", ""),
                    "answer": answer
                })
        
        return findings

