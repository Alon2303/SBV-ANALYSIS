"""Main SBV Protocol orchestrator - Steps 0-8."""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from .constriction import calculate_constriction_index
from .readiness import calculate_readiness_index
from .likely_lovely import calculate_likely_lovely
from ..research import CompanyResearcher
from ..storage.repository import AnalysisRepository

logger = logging.getLogger(__name__)


class SBVProtocol:
    """
    Main SBV Protocol implementation.
    
    Orchestrates the complete analysis flow:
    - Step 0-2: Research & data gathering
    - Step 3-5: System analysis & bottleneck identification
    - Step 6-7: Readiness & constriction calculation
    - Step 8: Final judgment & output
    """
    
    def __init__(self, researcher: Optional[CompanyResearcher] = None):
        self.researcher = researcher or CompanyResearcher()
    
    async def analyze_company(
        self,
        company_name: str,
        homepage: Optional[str] = None,
        repository: Optional[AnalysisRepository] = None
    ) -> Dict[str, Any]:
        """
        Run complete SBV analysis on a company.
        
        Args:
            company_name: Name of the company
            homepage: Optional homepage URL
            repository: Optional database repository for persistence
        
        Returns:
            Complete SBV analysis result matching sbv_tiny_schema.json
        """
        logger.info(f"Starting SBV analysis for {company_name}")
        
        try:
            # Step 0-2: Research & data gathering
            research_data = await self.researcher.research_company(
                company_name,
                homepage
            )
            
            company_info = research_data["company_info"]
            
            if "error" in company_info:
                raise ValueError(f"Research failed: {company_info['error']}")
            
            # Step 3-5: Bottleneck identification
            logger.info("Identifying bottlenecks...")
            bottlenecks = await self.researcher.analyze_bottlenecks(
                company_info,
                research_data
            )
            
            # Step 6: Readiness scoring
            logger.info("Scoring readiness levels...")
            readiness_scores = await self.researcher.score_readiness(company_info)
            
            # Step 7: Likely & Lovely scoring
            logger.info("Scoring Likely & Lovely...")
            likely_lovely_scores = await self.researcher.score_likely_lovely(
                company_info,
                research_data["scraped_content"]
            )
            
            # Calculate Constriction Index
            logger.info("Calculating Constriction Index...")
            ci_result = calculate_constriction_index(bottlenecks)
            
            # Calculate Readiness Index
            logger.info("Calculating Readiness Index...")
            ri_result = calculate_readiness_index(
                TRL_raw=readiness_scores["TRL_raw"],
                IRL_raw=readiness_scores["IRL_raw"],
                ORL_raw=readiness_scores["ORL_raw"],
                RCL_raw=readiness_scores["RCL_raw"],
                bottlenecks=bottlenecks,
                CI_fix=ci_result["CI_fix"]
            )
            
            # Calculate Likely & Lovely
            logger.info("Calculating Likely & Lovely metrics...")
            ll_result = calculate_likely_lovely(
                E=likely_lovely_scores["E"],
                T=likely_lovely_scores["T"],
                SP=likely_lovely_scores["SP"],
                LV=likely_lovely_scores["LV"]
            )
            
            # Build citations from research
            citations = self._build_citations(research_data)
            
            # Step 8: Build final result
            as_of_date = datetime.now().strftime("%Y-%m-%d")
            analysis_run_id = f"{company_name.lower().replace(' ', '_')}_{as_of_date}"
            
            # Config hash
            config_data = {
                "version": "sbv_v2_likely_lovely",
                "date": as_of_date,
                "alpha": 0.25
            }
            
            if repository:
                config_hash = repository.generate_config_hash(config_data)
            else:
                import hashlib
                import json
                config_hash = hashlib.sha256(
                    json.dumps(config_data, sort_keys=True).encode()
                ).hexdigest()
            
            result = {
                "company": company_name,
                "homepage": research_data["homepage"] or "",
                "as_of_date": as_of_date,
                "analysis_run_id": analysis_run_id,
                "config_hash": config_hash,
                "constriction": ci_result,
                "readiness": ri_result,
                "likely_lovely": ll_result,
                "bottlenecks": bottlenecks,
                "citations": citations,
                "wayback": {
                    "snapshot_url": None,
                    "snapshot_datetime": None,
                    "note": "Wayback lookup not implemented in this version"
                }
            }
            
            logger.info(f"Analysis complete for {company_name}")
            logger.info(f"  CI: {ci_result['CI_fix']:.3f}")
            logger.info(f"  RI: {ri_result['RI']:.3f}")
            logger.info(f"  RI_skeptical: {ri_result['RI_skeptical']:.3f}")
            logger.info(f"  CCF: {ll_result['CCF']:.3f}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error analyzing {company_name}: {str(e)}", exc_info=True)
            raise
    
    def _build_citations(self, research_data: Dict[str, Any]) -> list:
        """Build citations list from research data."""
        citations = []
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Add homepage
        if research_data.get("homepage"):
            citations.append({
                "claim": "Company homepage (value prop & services)",
                "url": research_data["homepage"],
                "date_seen": today
            })
        
        # Add scraped URLs
        for content in research_data.get("scraped_content", []):
            if content.get("success") and content.get("url"):
                title = content.get("title", "Source")
                citations.append({
                    "claim": f"Source: {title[:100]}",
                    "url": content["url"],
                    "date_seen": today
                })
        
        return citations

