"""Crunchbase startup database driver."""
import asyncio
import logging
from typing import Dict, Any, Optional

import requests

from ..base import BaseDriver

logger = logging.getLogger(__name__)


class CrunchbaseDriver(BaseDriver):
    """
    Driver for Crunchbase API.
    
    Crunchbase is the leading database for startup information:
    - Funding rounds and amounts
    - Investors and board members
    - Employee count and growth
    - Acquisitions and exits
    - Industry classification
    
    Pricing:
    - Free tier: Basic company info (limited)
    - Starter: $29/month
    - Pro: $49/month
    
    Docs: https://data.crunchbase.com/docs
    """
    
    API_BASE = "https://api.crunchbase.com/api/v4"
    
    @property
    def name(self) -> str:
        return "crunchbase"
    
    @property
    def display_name(self) -> str:
        return "Crunchbase"
    
    @property
    def description(self) -> str:
        return "Startup database: funding, investors, employees (Free tier available)"
    
    def requires_api_key(self) -> bool:
        return True
    
    async def _fetch_data(
        self,
        company_name: str,
        homepage: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch company data from Crunchbase.
        
        Args:
            company_name: Name of the company
            homepage: Optional homepage URL
        
        Returns:
            Dictionary with company data
        """
        self.set_progress(10.0)
        
        result = {
            "company_name": company_name,
            "found": False,
            "profile": None,
            "funding": [],
            "investors": [],
            "total_funding": None,
            "employee_count": None,
            "founded_date": None
        }
        
        try:
            # Step 1: Search for the company
            self.set_progress(30.0)
            search_results = await asyncio.to_thread(
                self._search_company,
                company_name
            )
            
            if not search_results:
                result["error"] = f"Company '{company_name}' not found in Crunchbase"
                logger.warning(f"Crunchbase: Company not found - {company_name}")
                return result
            
            # Get first result (usually most relevant)
            company_uuid = search_results[0]["uuid"]
            result["found"] = True
            result["crunchbase_url"] = f"https://www.crunchbase.com/organization/{search_results[0]['identifier']['value']}"
            
            # Step 2: Fetch detailed company info
            self.set_progress(60.0)
            company_data = await asyncio.to_thread(
                self._get_company_details,
                company_uuid
            )
            
            # Parse company data
            properties = company_data.get("properties", {})
            result["profile"] = {
                "name": properties.get("name"),
                "description": properties.get("short_description"),
                "website": properties.get("website", {}).get("value"),
                "founded_on": properties.get("founded_on", {}).get("value"),
                "employee_count": properties.get("num_employees_enum"),
                "company_type": properties.get("company_type"),
                "status": properties.get("status"),
                "categories": [cat.get("value") for cat in properties.get("categories", [])],
                "location": properties.get("location_identifiers", [{}])[0].get("value") if properties.get("location_identifiers") else None
            }
            
            result["founded_date"] = result["profile"]["founded_on"]
            result["employee_count"] = result["profile"]["employee_count"]
            
            # Step 3: Fetch funding data
            self.set_progress(80.0)
            funding_data = company_data.get("cards", {}).get("funding_rounds", {}).get("entities", [])
            
            total_funding_usd = 0
            for round_data in funding_data:
                round_props = round_data.get("properties", {})
                amount = round_props.get("money_raised", {})
                
                funding_round = {
                    "round_type": round_props.get("funding_type"),
                    "announced_on": round_props.get("announced_on", {}).get("value"),
                    "amount_usd": amount.get("value"),
                    "currency": amount.get("currency"),
                    "investor_count": round_props.get("num_investors"),
                }
                result["funding"].append(funding_round)
                
                if amount.get("value_usd"):
                    total_funding_usd += amount["value_usd"]
            
            result["total_funding"] = total_funding_usd
            result["funding_rounds_count"] = len(result["funding"])
            
            # Step 4: Extract investors
            investors_data = company_data.get("cards", {}).get("investors", {}).get("entities", [])
            result["investors"] = [
                {
                    "name": inv.get("properties", {}).get("identifier", {}).get("value"),
                    "type": inv.get("properties", {}).get("investor_type")
                }
                for inv in investors_data[:10]  # Limit to top 10
            ]
            
            logger.info(
                f"✅ Crunchbase: Found {company_data.get('properties', {}).get('name')} "
                f"with {result['funding_rounds_count']} funding rounds"
            )
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                result["error"] = "Invalid Crunchbase API key"
            elif e.response.status_code == 403:
                result["error"] = "Crunchbase API access denied (subscription required?)"
            elif e.response.status_code == 404:
                result["error"] = "Company not found"
            else:
                result["error"] = f"HTTP error: {e.response.status_code}"
            logger.error(f"Crunchbase API error: {result['error']}")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Crunchbase fetch failed: {e}", exc_info=True)
        
        return result
    
    def _search_company(self, company_name: str) -> List[Dict[str, Any]]:
        """Search for a company by name."""
        endpoint = f"{self.API_BASE}/autocompletes"
        
        params = {
            "query": company_name,
            "collection_ids": "organizations",
            "limit": 5
        }
        
        headers = {
            "X-cb-user-key": self.api_key
        }
        
        response = requests.get(
            endpoint,
            params=params,
            headers=headers,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get("entities", [])
    
    def _get_company_details(self, company_uuid: str) -> Dict[str, Any]:
        """Get detailed company information."""
        endpoint = f"{self.API_BASE}/entities/organizations/{company_uuid}"
        
        # Specify which cards (data sections) to include
        params = {
            "card_ids": "funding_rounds,investors,founders",
            "field_ids": "short_description,website,founded_on,num_employees_enum,categories,location_identifiers,company_type,status"
        }
        
        headers = {
            "X-cb-user-key": self.api_key
        }
        
        response = requests.get(
            endpoint,
            params=params,
            headers=headers,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        return response.json()

