"""Wayback Machine driver for fetching historical website snapshots."""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from urllib.parse import quote

import requests

from ..base import BaseDriver

logger = logging.getLogger(__name__)


class WaybackDriver(BaseDriver):
    """
    Driver for Internet Archive Wayback Machine.
    
    Fetches historical snapshots of company websites to track:
    - Company age (first appearance)
    - Website evolution
    - Funding announcements over time
    - Historical claims vs. current claims
    
    API Docs: https://archive.org/help/wayback_api.php
    FREE - No API key required
    """
    
    @property
    def name(self) -> str:
        return "wayback"
    
    @property
    def display_name(self) -> str:
        return "Wayback Machine"
    
    @property
    def description(self) -> str:
        return "Historical website snapshots from Internet Archive (FREE)"
    
    def requires_api_key(self) -> bool:
        return False  # Wayback Machine is completely free
    
    async def _fetch_data(
        self,
        company_name: str,
        homepage: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch historical snapshots from Wayback Machine.
        
        Args:
            company_name: Name of the company
            homepage: Company homepage URL
        
        Returns:
            Dictionary with snapshot data
        """
        if not homepage:
            # Try to construct likely URL
            domain = company_name.lower().replace(' ', '').replace('corp', '').replace('inc', '')
            homepage = f"https://www.{domain}.com"
            logger.info(f"No homepage provided, guessing: {homepage}")
        
        self.set_progress(10.0)
        
        # Clean URL
        homepage = homepage.strip()
        if not homepage.startswith(('http://', 'https://')):
            homepage = 'https://' + homepage
        
        result = {
            "url": homepage,
            "company_name": company_name,
            "snapshots": [],
            "first_snapshot": None,
            "latest_snapshot": None,
            "total_snapshots": 0,
            "company_age_days": None,
            "available": False
        }
        
        try:
            # Step 1: Check availability
            self.set_progress(30.0)
            availability = await asyncio.to_thread(
                self._check_availability,
                homepage
            )
            
            if not availability.get("available"):
                result["error"] = "No snapshots found in Wayback Machine"
                result["message"] = f"The website {homepage} has not been archived by the Wayback Machine."
                return result
            
            result["available"] = True
            
            # Step 2: Get snapshot timeline
            self.set_progress(60.0)
            snapshots = await asyncio.to_thread(
                self._get_snapshots,
                homepage
            )
            
            result["snapshots"] = snapshots
            result["total_snapshots"] = len(snapshots)
            
            if snapshots:
                result["first_snapshot"] = snapshots[0]
                result["latest_snapshot"] = snapshots[-1]
                
                # Calculate company age
                first_date = datetime.strptime(snapshots[0]["timestamp"][:8], "%Y%m%d")
                age_days = (datetime.now() - first_date).days
                result["company_age_days"] = age_days
                result["company_age_years"] = round(age_days / 365.25, 1)
                
                logger.info(
                    f"✅ {self.display_name}: Found {len(snapshots)} snapshots, "
                    f"company age: {result['company_age_years']} years"
                )
            
            self.set_progress(90.0)
            
            # Step 3: Fetch first and latest snapshot content (optional)
            # This could be used for diff analysis
            result["first_snapshot_url"] = self._build_snapshot_url(
                homepage, snapshots[0]["timestamp"]
            ) if snapshots else None
            result["latest_snapshot_url"] = self._build_snapshot_url(
                homepage, snapshots[-1]["timestamp"]
            ) if snapshots else None
            
        except Exception as e:
            logger.error(f"Wayback Machine fetch failed: {e}")
            result["error"] = str(e)
        
        return result
    
    def _check_availability(self, url: str) -> Dict[str, Any]:
        """
        Check if URL is available in Wayback Machine.
        
        API endpoint: https://archive.org/wayback/available?url={url}
        """
        api_url = f"https://archive.org/wayback/available?url={quote(url)}"
        
        response = requests.get(api_url, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("archived_snapshots") and data["archived_snapshots"].get("closest"):
            closest = data["archived_snapshots"]["closest"]
            return {
                "available": True,
                "url": closest.get("url"),
                "timestamp": closest.get("timestamp"),
                "status": closest.get("status")
            }
        
        return {"available": False}
    
    def _get_snapshots(self, url: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get list of all snapshots for a URL.
        
        Uses CDX API: https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server
        """
        cdx_api = "https://web.archive.org/cdx/search/cdx"
        params = {
            "url": url,
            "output": "json",
            "fl": "timestamp,statuscode,mimetype,length",
            "filter": "statuscode:200",  # Only successful captures
            "collapse": "timestamp:8",    # One per day
            "limit": limit
        }
        
        response = requests.get(cdx_api, params=params, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        
        # Skip header row
        if len(data) > 1:
            data = data[1:]
        
        snapshots = []
        for row in data:
            if len(row) >= 4:
                snapshots.append({
                    "timestamp": row[0],
                    "status_code": row[1],
                    "mime_type": row[2],
                    "length": row[3],
                    "date": datetime.strptime(row[0][:8], "%Y%m%d").strftime("%Y-%m-%d"),
                    "url": self._build_snapshot_url(url, row[0])
                })
        
        return snapshots
    
    def _build_snapshot_url(self, url: str, timestamp: str) -> str:
        """Build URL to view a specific snapshot."""
        return f"https://web.archive.org/web/{timestamp}/{url}"

