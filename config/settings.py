"""
Configuration settings for the Agentic AI system
"""

import os
from typing import Optional


class Settings:
    """Application settings"""
    
    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # Model Configuration
    BOSS_MODEL: str = os.getenv("BOSS_MODEL", "gpt-4")
    RESEARCH_MODEL: str = os.getenv("RESEARCH_MODEL", "gpt-4")
    WRITING_MODEL: str = os.getenv("WRITING_MODEL", "gpt-4")
    CODE_MODEL: str = os.getenv("CODE_MODEL", "gpt-4")
    AGGREGATOR_MODEL: str = os.getenv("AGGREGATOR_MODEL", "gpt-4")
    
    # Temperature Settings
    BOSS_TEMPERATURE: float = float(os.getenv("BOSS_TEMPERATURE", "0"))
    RESEARCH_TEMPERATURE: float = float(os.getenv("RESEARCH_TEMPERATURE", "0.3"))
    WRITING_TEMPERATURE: float = float(os.getenv("WRITING_TEMPERATURE", "0.7"))
    CODE_TEMPERATURE: float = float(os.getenv("CODE_TEMPERATURE", "0.2"))
    AGGREGATOR_TEMPERATURE: float = float(os.getenv("AGGREGATOR_TEMPERATURE", "0.5"))
    
    # System Configuration
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    TIMEOUT: int = int(os.getenv("TIMEOUT", "120"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    VERBOSE: bool = os.getenv("VERBOSE", "false").lower() == "true"


settings = Settings()
