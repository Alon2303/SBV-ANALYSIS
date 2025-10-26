"""Company researcher using AI and web scraping."""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from .llm_client import LLMClient
from .web_scraper import WebScraper, scrape_with_requests
from .prompts import (
    RESEARCH_SYSTEM_PROMPT,
    BOTTLENECK_ANALYSIS_PROMPT,
    READINESS_SCORING_PROMPT,
    LIKELY_LOVELY_SCORING_PROMPT,
)

logger = logging.getLogger(__name__)


class CompanyResearcher:
    """AI-powered company researcher for SBV analysis."""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
    
    async def research_company(
        self,
        company_name: str,
        homepage: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Conduct comprehensive research on a company.
        
        Args:
            company_name: Name of the company
            homepage: Optional homepage URL
        
        Returns:
            Dict with research results including:
            - company info
            - web search results
            - scraped content
            - extracted claims
            - citations
        """
        logger.info(f"Researching {company_name}...")
        
        # Step 1: Web search for company information
        search_results = await self._search_company(company_name, homepage)
        
        # Step 2: Scrape relevant URLs
        scraped_content = await self._scrape_urls(search_results["urls"])
        
        # Step 3: Extract structured information using LLM
        company_info = await self._extract_company_info(
            company_name,
            search_results,
            scraped_content
        )
        
        return {
            "company_name": company_name,
            "homepage": homepage or company_info.get("homepage"),
            "search_results": search_results,
            "scraped_content": scraped_content,
            "company_info": company_info,
            "research_date": datetime.now().isoformat()
        }
    
    async def _search_company(
        self,
        company_name: str,
        homepage: Optional[str]
    ) -> Dict[str, Any]:
        """
        Search for company information online.
        
        For now, uses homepage and constructs likely URLs.
        In production, would use Tavily or SerpAPI.
        """
        urls = []
        
        if homepage:
            urls.append(homepage)
        
        # Construct likely URLs for common sources
        # In production, use actual search API
        search_queries = [
            f"{company_name} company website",
            f"{company_name} technology",
            f"{company_name} funding news",
        ]
        
        return {
            "queries": search_queries,
            "urls": urls,
            "homepage": homepage
        }
    
    async def _scrape_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape multiple URLs."""
        if not urls:
            return []
        
        try:
            async with WebScraper() as scraper:
                results = await scraper.scrape_multiple(urls[:5])  # Limit to 5 URLs
            return results
        except Exception as e:
            logger.warning(f"Playwright scraping failed: {e}. Falling back to requests.")
            # Fallback to simple requests
            results = []
            for url in urls[:5]:
                result = await asyncio.to_thread(scrape_with_requests, url)
                results.append(result)
            return results
    
    async def _extract_company_info(
        self,
        company_name: str,
        search_results: Dict[str, Any],
        scraped_content: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract structured company information using LLM."""
        
        # Combine all scraped text
        all_text = []
        for content in scraped_content:
            if content.get("text_content"):
                all_text.append(f"URL: {content['url']}\n{content['text_content'][:5000]}")
        
        combined_text = "\n\n---\n\n".join(all_text)
        
        if not combined_text.strip():
            logger.warning(f"No content scraped for {company_name}")
            return {
                "error": "No content could be scraped",
                "company_name": company_name
            }
        
        # Prompt for extracting company information
        prompt = f"""You are analyzing the company: {company_name}

Based on the following web content, extract structured information about this company:

{combined_text[:20000]}

Extract the following information in JSON format:
{{
    "company_name": "Full company name",
    "homepage": "Company homepage URL",
    "description": "Brief description of what the company does",
    "value_proposition": "Main value proposition or claims",
    "technology": "Core technology or innovation",
    "industry": "Primary industry/sector",
    "stage": "Company stage (e.g., prototype, pilot, production)",
    "technical_claims": ["List of specific technical claims with numbers if available"],
    "social_proof": {{
        "accelerators": ["List of accelerators/incubators"],
        "grants": ["List of grants or awards"],
        "customers": ["List of known customers or pilots"],
        "investors": ["List of investors if mentioned"],
        "advisors": ["List of notable advisors if mentioned"]
    }},
    "evidence_urls": ["List of URLs with supporting evidence"]
}}

Be thorough and extract specific claims with numbers when available.
"""
        
        try:
            response = await asyncio.to_thread(
                self.llm.complete,
                prompt,
                system_prompt=RESEARCH_SYSTEM_PROMPT,
                json_mode=True
            )
            info = self.llm.extract_json(response)
            return info
        except Exception as e:
            logger.error(f"Error extracting company info: {e}")
            return {
                "error": str(e),
                "company_name": company_name
            }
    
    async def analyze_bottlenecks(
        self,
        company_info: Dict[str, Any],
        research_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify and score bottlenecks using LLM."""
        
        prompt = BOTTLENECK_ANALYSIS_PROMPT.format(
            company_name=company_info.get("company_name", "Unknown"),
            description=company_info.get("description", ""),
            technology=company_info.get("technology", ""),
            stage=company_info.get("stage", ""),
            claims="\n".join(company_info.get("technical_claims", []))
        )
        
        try:
            response = await asyncio.to_thread(
                self.llm.complete,
                prompt,
                system_prompt=RESEARCH_SYSTEM_PROMPT,
                json_mode=True
            )
            result = self.llm.extract_json(response)
            return result.get("bottlenecks", [])
        except Exception as e:
            logger.error(f"Error analyzing bottlenecks: {e}")
            return []
    
    async def score_readiness(
        self,
        company_info: Dict[str, Any]
    ) -> Dict[str, float]:
        """Score readiness levels (TRL, IRL, ORL, RCL) using LLM."""
        
        prompt = READINESS_SCORING_PROMPT.format(
            company_name=company_info.get("company_name", "Unknown"),
            description=company_info.get("description", ""),
            technology=company_info.get("technology", ""),
            stage=company_info.get("stage", ""),
            claims="\n".join(company_info.get("technical_claims", []))
        )
        
        try:
            response = await asyncio.to_thread(
                self.llm.complete,
                prompt,
                system_prompt=RESEARCH_SYSTEM_PROMPT,
                json_mode=True
            )
            scores = self.llm.extract_json(response)
            return {
                "TRL_raw": float(scores.get("TRL", 3.0)),
                "IRL_raw": float(scores.get("IRL", 3.0)),
                "ORL_raw": float(scores.get("ORL", 3.0)),
                "RCL_raw": float(scores.get("RCL", 1.0)),
                "reasoning": scores.get("reasoning", "")
            }
        except Exception as e:
            logger.error(f"Error scoring readiness: {e}")
            return {
                "TRL_raw": 3.0,
                "IRL_raw": 3.0,
                "ORL_raw": 3.0,
                "RCL_raw": 1.0,
                "reasoning": f"Error: {e}"
            }
    
    async def score_likely_lovely(
        self,
        company_info: Dict[str, Any],
        scraped_content: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Score Evidence, Theory, Social Proof, and Lovely value using LLM."""
        
        # Count evidence sources
        evidence_count = len([c for c in scraped_content if c.get("success")])
        
        prompt = LIKELY_LOVELY_SCORING_PROMPT.format(
            company_name=company_info.get("company_name", "Unknown"),
            description=company_info.get("description", ""),
            technical_claims="\n".join(company_info.get("technical_claims", [])),
            social_proof=str(company_info.get("social_proof", {})),
            evidence_sources=evidence_count
        )
        
        try:
            response = await asyncio.to_thread(
                self.llm.complete,
                prompt,
                system_prompt=RESEARCH_SYSTEM_PROMPT,
                json_mode=True
            )
            scores = self.llm.extract_json(response)
            return {
                "E": int(scores.get("E", 2)),
                "T": int(scores.get("T", 3)),
                "SP": int(scores.get("SP", 2)),
                "LV": int(scores.get("LV", 3)),
                "reasoning": scores.get("reasoning", "")
            }
        except Exception as e:
            logger.error(f"Error scoring Likely/Lovely: {e}")
            return {
                "E": 2,
                "T": 3,
                "SP": 2,
                "LV": 3,
                "reasoning": f"Error: {e}"
            }

