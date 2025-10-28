"""Configuration management for SBV Pipeline."""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    
    # Database
    database_url: str = "sqlite:///data/sbv.db"
    
    # Google Sheets
    google_sheets_credentials_path: Optional[str] = None
    
    # Application
    environment: str = "development"
    log_level: str = "INFO"
    max_concurrent_analyses: int = 10
    
    # LLM Settings
    default_llm_provider: str = "openai"  # "openai" or "anthropic"
    default_model: str = "gpt-4-turbo-preview"
    temperature: float = 0.3
    max_tokens: int = 4000
    
    # Paths
    project_root: Path = Path(__file__).parent.parent
    data_dir: Path = project_root / "data"
    input_dir: Path = data_dir / "input"
    output_dir: Path = data_dir / "output"
    schema_dir: Path = project_root / "schemas"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)


# Global settings instance
settings = Settings()

