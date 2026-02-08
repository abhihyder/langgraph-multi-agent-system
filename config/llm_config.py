"""
LLM Provider Configuration
Centralized configuration for all LLM providers and models
"""

import os
from typing import Dict, Any
from functools import lru_cache


class LLMConfig:
    """LLM provider and model configuration"""
    
    # API Keys for different providers
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")
    GOOGLE_API_KEY: str | None = os.getenv("GOOGLE_API_KEY")
    
    # Default provider for all agents (can be overridden per agent)
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "openai")
    
    # Supported providers and their models
    SUPPORTED_PROVIDERS: Dict[str, Dict[str, Any]] = {
        "openai": {
            "models": [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo"
            ],
            "default_model": "gpt-4o-mini"
        },
        "anthropic": {
            "models": [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ],
            "default_model": "claude-3-5-sonnet-20241022"
        },
        "google": {
            "models": [
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-2.5-flash",
                "gemini-1.0-pro"
            ],
            "default_model": "gemini-2.5-flash"
        }
    }
    
    # Agent-specific provider and model configuration
    # Format: provider:model or just provider (uses default model)
    ORCHESTRATOR_LLM: str = os.getenv("ORCHESTRATOR_LLM", "openai:gpt-4o-mini")
    RESEARCH_LLM: str = os.getenv("RESEARCH_LLM", "openai:gpt-4o-mini")
    WRITING_LLM: str = os.getenv("WRITING_LLM", "openai:gpt-4o-mini")
    CODE_LLM: str = os.getenv("CODE_LLM", "openai:gpt-4o-mini")
    GENERAL_LLM: str = os.getenv("GENERAL_LLM", "openai:gpt-4o-mini")
    AGGREGATOR_LLM: str = os.getenv("AGGREGATOR_LLM", "openai:gpt-4o-mini")
    
    # Temperature Settings
    # Control randomness in responses (0.0 = deterministic, 1.0 = creative)
    ORCHESTRATOR_TEMPERATURE: float = float(os.getenv("ORCHESTRATOR_TEMPERATURE", "0"))
    RESEARCH_TEMPERATURE: float = float(os.getenv("RESEARCH_TEMPERATURE", "0.3"))
    WRITING_TEMPERATURE: float = float(os.getenv("WRITING_TEMPERATURE", "0.7"))
    CODE_TEMPERATURE: float = float(os.getenv("CODE_TEMPERATURE", "0.2"))
    AGGREGATOR_TEMPERATURE: float = float(os.getenv("AGGREGATOR_TEMPERATURE", "0.5"))
    
    @classmethod
    def get_provider_config(cls, provider: str) -> Dict[str, Any] | None:
        """
        Get configuration for a specific provider.
        
        Args:
            provider: Provider name (openai, anthropic, google)
            
        Returns:
            Provider configuration dict or None if not found
        """
        return cls.SUPPORTED_PROVIDERS.get(provider.lower())
    
    @classmethod
    def is_provider_supported(cls, provider: str) -> bool:
        """
        Check if a provider is supported.
        
        Args:
            provider: Provider name
            
        Returns:
            True if supported, False otherwise
        """
        return provider.lower() in cls.SUPPORTED_PROVIDERS
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """
        Get list of all supported provider names.
        
        Returns:
            List of provider names
        """
        return list(cls.SUPPORTED_PROVIDERS.keys())
    
    @classmethod
    def has_api_key(cls, provider: str) -> bool:
        """
        Check if API key is configured for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            True if API key is set, False otherwise
        """
        provider = provider.lower()
        if provider == "openai":
            return cls.OPENAI_API_KEY is not None
        elif provider == "anthropic":
            return cls.ANTHROPIC_API_KEY is not None
        elif provider == "google":
            return cls.GOOGLE_API_KEY is not None
        return False


@lru_cache()
def get_llm_config() -> LLMConfig:
    """Get cached LLM configuration instance"""
    return LLMConfig()


# Legacy support
llm_config = get_llm_config()
