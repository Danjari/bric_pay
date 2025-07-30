import os
from typing import List
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Database Configuration
    database_url: str = "sqlite:///./bric_pay.db"
    
    # Security
    secret_key: str = "bric-pay-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application Settings
    debug: bool = True
    log_level: str = "INFO"
    
    # API Configuration
    api_v1_str: str = "/api/v1"
    project_name: str = "Bric Pay API"
    version: str = "1.0.0"
    
    # CORS Settings
    allowed_hosts: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Database Pool Settings
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create settings instance
settings = Settings() 