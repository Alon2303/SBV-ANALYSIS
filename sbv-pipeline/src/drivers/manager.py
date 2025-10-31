"""Driver manager for orchestrating multiple data sources."""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BaseDriver, DriverResult, DriverStatus
from .wayback import WaybackDriver
from .tavily import TavilyDriver
from .crunchbase import CrunchbaseDriver
from .serpapi import SerpAPIDriver

logger = logging.getLogger(__name__)


class DriverManager:
    """
    Manages and orchestrates multiple data source drivers.
    
    Features:
    - Runs drivers in parallel (async)
    - Aggregates results from all sources
    - Tracks overall progress
    - Handles driver failures gracefully
    - Supports enable/disable per driver
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize driver manager.
        
        Args:
            config: Configuration dict with API keys and enable flags
                   Format: {
                       "wayback": {"enabled": True},
                       "tavily": {"enabled": True, "api_key": "..."},
                       ...
                   }
        """
        self.config = config or {}
        self.drivers: Dict[str, BaseDriver] = {}
        self._results: Dict[str, DriverResult] = {}
        
        # Initialize all drivers
        self._initialize_drivers()
    
    def _initialize_drivers(self):
        """Initialize all available drivers based on config."""
        
        # Wayback Machine (no API key needed)
        wayback_config = self.config.get("wayback", {})
        self.drivers["wayback"] = WaybackDriver(
            is_enabled=wayback_config.get("enabled", True)
        )
        
        # Tavily
        tavily_config = self.config.get("tavily", {})
        self.drivers["tavily"] = TavilyDriver(
            api_key=tavily_config.get("api_key"),
            is_enabled=tavily_config.get("enabled", False)  # Disabled by default (needs key)
        )
        
        # Crunchbase
        crunchbase_config = self.config.get("crunchbase", {})
        self.drivers["crunchbase"] = CrunchbaseDriver(
            api_key=crunchbase_config.get("api_key"),
            is_enabled=crunchbase_config.get("enabled", False)  # Disabled by default (needs key)
        )
        
        # SerpAPI
        serpapi_config = self.config.get("serpapi", {})
        self.drivers["serpapi"] = SerpAPIDriver(
            api_key=serpapi_config.get("api_key"),
            is_enabled=serpapi_config.get("enabled", False)  # Disabled by default (needs key)
        )
        
        logger.info(f"Initialized {len(self.drivers)} drivers")
        
        # Log status of each driver
        for name, driver in self.drivers.items():
            if driver.is_enabled:
                if driver.status == DriverStatus.MISSING_API_KEY:
                    logger.warning(f"  ⚠️  {driver.display_name}: Enabled but missing API key")
                else:
                    logger.info(f"  ✅ {driver.display_name}: Enabled")
            else:
                logger.info(f"  ⏸️  {driver.display_name}: Disabled")
    
    def get_driver(self, name: str) -> Optional[BaseDriver]:
        """Get a specific driver by name."""
        return self.drivers.get(name)
    
    def list_drivers(self) -> List[Dict[str, Any]]:
        """List all drivers with their status."""
        return [
            {
                "name": driver.name,
                "display_name": driver.display_name,
                "description": driver.description,
                "is_enabled": driver.is_enabled,
                "requires_api_key": driver.requires_api_key(),
                "has_api_key": bool(driver.api_key),
                "status": driver.status.value,
                "progress": driver.progress
            }
            for driver in self.drivers.values()
        ]
    
    def get_enabled_drivers(self) -> List[BaseDriver]:
        """Get list of enabled drivers."""
        return [
            driver for driver in self.drivers.values()
            if driver.is_enabled and driver.status != DriverStatus.MISSING_API_KEY
        ]
    
    async def run_all(
        self,
        company_name: str,
        homepage: Optional[str] = None,
        **kwargs
    ) -> Dict[str, DriverResult]:
        """
        Run all enabled drivers in parallel.
        
        Args:
            company_name: Name of the company
            homepage: Optional homepage URL
            **kwargs: Additional parameters
        
        Returns:
            Dictionary mapping driver name to DriverResult
        """
        enabled_drivers = self.get_enabled_drivers()
        
        if not enabled_drivers:
            logger.warning("No drivers enabled! Enable at least one data source.")
            return {}
        
        logger.info(
            f"🚀 Starting parallel research for '{company_name}' "
            f"with {len(enabled_drivers)} sources"
        )
        
        start_time = datetime.now()
        
        # Run all drivers in parallel
        tasks = [
            driver.run(company_name, homepage, **kwargs)
            for driver in enabled_drivers
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Map results back to driver names
        self._results = {}
        for driver, result in zip(enabled_drivers, results):
            if isinstance(result, Exception):
                logger.error(f"Driver {driver.name} crashed: {result}")
                self._results[driver.name] = DriverResult(
                    source_name=driver.name,
                    status=DriverStatus.FAILED,
                    error=str(result),
                    started_at=start_time,
                    completed_at=datetime.now()
                )
            else:
                self._results[driver.name] = result
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Log summary
        successful = sum(1 for r in self._results.values() if r.status == DriverStatus.COMPLETED)
        failed = sum(1 for r in self._results.values() if r.status == DriverStatus.FAILED)
        
        logger.info(
            f"✅ Parallel research complete in {duration:.1f}s: "
            f"{successful} successful, {failed} failed"
        )
        
        return self._results
    
    async def run_single(
        self,
        driver_name: str,
        company_name: str,
        homepage: Optional[str] = None,
        **kwargs
    ) -> Optional[DriverResult]:
        """
        Run a single driver by name.
        
        Args:
            driver_name: Name of the driver (e.g., 'wayback', 'tavily')
            company_name: Name of the company
            homepage: Optional homepage URL
            **kwargs: Additional parameters
        
        Returns:
            DriverResult or None if driver not found
        """
        driver = self.get_driver(driver_name)
        
        if not driver:
            logger.error(f"Driver '{driver_name}' not found")
            return None
        
        if not driver.is_enabled:
            logger.warning(f"Driver '{driver_name}' is disabled")
            return DriverResult(
                source_name=driver_name,
                status=DriverStatus.DISABLED,
                error="Driver is disabled"
            )
        
        logger.info(f"Running single driver: {driver.display_name}")
        result = await driver.run(company_name, homepage, **kwargs)
        self._results[driver_name] = result
        
        return result
    
    def get_results(self) -> Dict[str, DriverResult]:
        """Get all results from the last run."""
        return self._results
    
    def get_result(self, driver_name: str) -> Optional[DriverResult]:
        """Get result from a specific driver."""
        return self._results.get(driver_name)
    
    def get_aggregate_progress(self) -> float:
        """Get overall progress across all enabled drivers."""
        enabled = self.get_enabled_drivers()
        if not enabled:
            return 0.0
        
        total_progress = sum(driver.progress for driver in enabled)
        return total_progress / len(enabled)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all driver statuses and results."""
        return {
            "total_drivers": len(self.drivers),
            "enabled_drivers": len(self.get_enabled_drivers()),
            "overall_progress": self.get_aggregate_progress(),
            "drivers": self.list_drivers(),
            "results": {
                name: result.to_dict()
                for name, result in self._results.items()
            }
        }
    
    def reset_all(self):
        """Reset all drivers to initial state."""
        for driver in self.drivers.values():
            driver.reset()
        self._results = {}
        logger.info("All drivers reset")

