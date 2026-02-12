"""Application configuration using Pydantic settings."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_prefix: str = "/api"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "sqlite:///./airwatch.db"
    
    # External APIs
    airnow_api_key: str = ""
    nws_user_agent: str = "AirWatch-Student-email@example.com"
    
    # Model Paths
    model_path: str = "backend/app/ml/artifacts/aqi_model.pkl"
    feature_list_path: str = "backend/app/ml/artifacts/feature_list.pkl"
    prediction_threshold: float = 0.40
    
    # Data Collection URLs
    epa_data_url: str = "https://www.epa.gov/outdoor-air-quality-data"
    openaq_api_url: str = "https://api.openaq.org/v2"
    nws_api_url: str = "https://api.weather.gov"
    
    # Scheduler
    enable_scheduler: bool = True
    update_time: str = "16:00"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
