"""Base driver interface for data sources."""
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List


logger = logging.getLogger(__name__)


class DriverStatus(Enum):
    """Driver execution status."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"
    MISSING_API_KEY = "missing_api_key"


@dataclass
class DriverResult:
    """Result from a driver execution."""
    source_name: str
    status: DriverStatus
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percent: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate execution duration."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "source_name": self.source_name,
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress_percent": self.progress_percent,
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata
        }


class BaseDriver(ABC):
    """
    Abstract base class for all data source drivers.
    
    Each driver represents a single data source (e.g., Tavily, Wayback, Crunchbase)
    and implements the logic to fetch and parse data from that source.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        is_enabled: bool = True,
        timeout: int = 60,
        max_retries: int = 3
    ):
        """
        Initialize driver.
        
        Args:
            api_key: API key for the source (if required)
            is_enabled: Whether this driver should run
            timeout: Timeout in seconds for requests
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key
        self.is_enabled = is_enabled
        self.timeout = timeout
        self.max_retries = max_retries
        
        self._progress = 0.0
        self._status = DriverStatus.IDLE
        self._result: Optional[DriverResult] = None
        
        # Validate API key requirement
        if self.requires_api_key() and not api_key:
            self._status = DriverStatus.MISSING_API_KEY
            logger.warning(f"{self.name}: API key required but not provided")
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this driver (e.g., 'wayback', 'tavily')."""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for UI display."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this driver does."""
        pass
    
    @abstractmethod
    def requires_api_key(self) -> bool:
        """Whether this driver requires an API key."""
        pass
    
    @property
    def progress(self) -> float:
        """Current progress (0-100)."""
        return self._progress
    
    @property
    def status(self) -> DriverStatus:
        """Current execution status."""
        return self._status
    
    def set_progress(self, percent: float):
        """Update progress percentage."""
        self._progress = max(0.0, min(100.0, percent))
    
    async def run(
        self,
        company_name: str,
        homepage: Optional[str] = None,
        **kwargs
    ) -> DriverResult:
        """
        Execute the driver to fetch data.
        
        Args:
            company_name: Name of the company to research
            homepage: Optional homepage URL
            **kwargs: Additional parameters specific to the driver
        
        Returns:
            DriverResult with fetched data or error
        """
        # Check if enabled
        if not self.is_enabled:
            return DriverResult(
                source_name=self.name,
                status=DriverStatus.DISABLED,
                error="Driver is disabled"
            )
        
        # Check for API key if required
        if self.requires_api_key() and not self.api_key:
            return DriverResult(
                source_name=self.name,
                status=DriverStatus.MISSING_API_KEY,
                error=f"API key required for {self.display_name}. Add {self.name.upper()}_API_KEY to your .env file."
            )
        
        # Initialize result
        result = DriverResult(
            source_name=self.name,
            status=DriverStatus.RUNNING,
            started_at=datetime.now()
        )
        self._result = result
        self._status = DriverStatus.RUNNING
        self.set_progress(0.0)
        
        logger.info(f"🔄 {self.display_name}: Starting research for '{company_name}'")
        
        try:
            # Execute the driver-specific logic
            data = await self._fetch_data(company_name, homepage, **kwargs)
            
            # Update result
            result.data = data
            result.status = DriverStatus.COMPLETED
            result.completed_at = datetime.now()
            result.progress_percent = 100.0
            
            self._status = DriverStatus.COMPLETED
            self.set_progress(100.0)
            
            logger.info(
                f"✅ {self.display_name}: Completed in {result.duration_seconds:.1f}s"
            )
            
        except asyncio.TimeoutError:
            error_msg = f"Timeout after {self.timeout}s"
            logger.error(f"❌ {self.display_name}: {error_msg}")
            result.status = DriverStatus.FAILED
            result.error = error_msg
            result.completed_at = datetime.now()
            self._status = DriverStatus.FAILED
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ {self.display_name}: {error_msg}", exc_info=True)
            result.status = DriverStatus.FAILED
            result.error = error_msg
            result.completed_at = datetime.now()
            self._status = DriverStatus.FAILED
        
        self._result = result
        return result
    
    @abstractmethod
    async def _fetch_data(
        self,
        company_name: str,
        homepage: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch data from the source (implemented by subclasses).
        
        Args:
            company_name: Name of the company
            homepage: Optional homepage URL
            **kwargs: Additional parameters
        
        Returns:
            Dictionary with fetched data
        
        Raises:
            Exception: If fetch fails
        """
        pass
    
    def get_result(self) -> Optional[DriverResult]:
        """Get the most recent result."""
        return self._result
    
    def reset(self):
        """Reset driver state."""
        self._progress = 0.0
        self._status = DriverStatus.IDLE
        self._result = None
    
    def __str__(self) -> str:
        return f"{self.display_name} ({self.name})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}' status={self.status.value}>"

