"""Configuration management for SBV Pipeline."""
import os
import tempfile
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


def is_streamlit_cloud() -> bool:
    """Detect if running on Streamlit Cloud."""
    # Streamlit Cloud sets specific environment variables
    return (
        os.getenv("STREAMLIT_RUNTIME_ENVIRONMENT") == "cloud" or
        os.getenv("STREAMLIT_SHARING_MODE") is not None or
        "/mount/src/" in os.getcwd()  # Streamlit Cloud path pattern
    )


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
    
    @property
    def data_dir(self) -> Path:
        """Get data directory - use temp dir on Streamlit Cloud."""
        if is_streamlit_cloud():
            # Use temp directory on Streamlit Cloud (writable)
            temp_dir = Path(tempfile.gettempdir()) / "sbv_data"
            temp_dir.mkdir(exist_ok=True)
            return temp_dir
        else:
            # Use project data directory locally
            data_dir = self.project_root / "data"
            data_dir.mkdir(exist_ok=True)
            return data_dir
    
    @property
    def input_dir(self) -> Path:
        """Get input directory."""
        input_dir = self.data_dir / "input"
        input_dir.mkdir(exist_ok=True, parents=True)
        return input_dir
    
    @property
    def output_dir(self) -> Path:
        """Get output directory."""
        output_dir = self.data_dir / "output"
        output_dir.mkdir(exist_ok=True, parents=True)
        return output_dir
    
    @property
    def schema_dir(self) -> Path:
        """Get schema directory."""
        return self.project_root / "schemas"
    
    @property
    def database_path(self) -> str:
        """Get absolute database path - use temp location on Streamlit Cloud."""
        db_file = self.data_dir / "sbv.db"
        return f"sqlite:///{db_file.absolute()}"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Log where data is being stored
        if is_streamlit_cloud():
            print(f"🌐 Running on Streamlit Cloud - using temp directory: {self.data_dir}")
        else:
            print(f"💻 Running locally - using project directory: {self.data_dir}")


# Global settings instance
settings = Settings()

