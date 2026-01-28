"""
Configuration settings for the Agentic AI system
"""

import os
from typing import Optional
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings with environment variable support"""
    
    # Application
    APP_NAME: str = "Multi-Agent AI System"
    VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Database Configuration (Laravel-style)
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_DATABASE: str = os.getenv("DB_DATABASE", "multiagent_ai")
    DB_USERNAME: str = os.getenv("DB_USERNAME", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")
    
    # Build DATABASE_URL from individual components
    # Can be overridden by setting DATABASE_URL directly
    @property
    def DATABASE_URL(self) -> str:
        """
        Construct database URL from individual components.
        Falls back to DATABASE_URL env var if set.
        """
        env_url = os.getenv("DATABASE_URL")
        if env_url:
            return env_url
        
        return f"postgresql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://localhost:8000/auth/google/callback"
    )
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # Model Configuration
    ORCHESTRATOR_MODEL: str = os.getenv("ORCHESTRATOR_MODEL", "gpt-4")
    RESEARCH_MODEL: str = os.getenv("RESEARCH_MODEL", "gpt-4")
    WRITING_MODEL: str = os.getenv("WRITING_MODEL", "gpt-4")
    CODE_MODEL: str = os.getenv("CODE_MODEL", "gpt-4")
    AGGREGATOR_MODEL: str = os.getenv("AGGREGATOR_MODEL", "gpt-4")
    
    # Temperature Settings
    ORCHESTRATOR_TEMPERATURE: float = float(os.getenv("ORCHESTRATOR_TEMPERATURE", "0"))
    RESEARCH_TEMPERATURE: float = float(os.getenv("RESEARCH_TEMPERATURE", "0.3"))
    WRITING_TEMPERATURE: float = float(os.getenv("WRITING_TEMPERATURE", "0.7"))
    CODE_TEMPERATURE: float = float(os.getenv("CODE_TEMPERATURE", "0.2"))
    AGGREGATOR_TEMPERATURE: float = float(os.getenv("AGGREGATOR_TEMPERATURE", "0.5"))
    
    # System Configuration
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    TIMEOUT: int = int(os.getenv("TIMEOUT", "120"))
    
    # CORS Configuration
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    VERBOSE: bool = os.getenv("VERBOSE", "false").lower() == "true"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Legacy support
settings = get_settings()
