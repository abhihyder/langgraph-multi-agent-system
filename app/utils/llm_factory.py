"""
LLM Factory - Creates LLM instances based on provider and model configuration
with LangSmith tracing support
"""

import logging
from typing import Optional, List, Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.callbacks import BaseCallbackHandler
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from config.llm_config import get_llm_config
from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def get_langsmith_callbacks() -> List[BaseCallbackHandler]:
    """
    Get LangSmith callback handlers if tracing is enabled.
    
    Returns:
        List of callback handlers for LangSmith tracing
    """
    callbacks = []
    
    # LangSmith tracing is automatically enabled via environment variables
    # No explicit callbacks needed - LangChain detects LANGCHAIN_TRACING_V2
    # But we can add custom callbacks if needed
    
    return callbacks


class LLMFactory:
    """Factory class for creating LLM instances based on provider and model"""
    
    @staticmethod
    def _parse_llm_config(llm_config: str) -> tuple[str, str]:
        """
        Parse LLM configuration string (internal helper).
        
        Args:
            llm_config: Format "provider:model" or "provider" (uses default model)
            
        Returns:
            Tuple of (provider, model)
            
        Examples:
            "openai:gpt-4o" -> ("openai", "gpt-4o")
            "anthropic" -> ("anthropic", "claude-3-5-sonnet-20241022")
            "google:gemini-1.5-pro" -> ("google", "gemini-1.5-pro")
        """
        config = get_llm_config()
        
        if ":" in llm_config:
            provider, model = llm_config.split(":", 1)
        else:
            provider = llm_config
            # Use default model for provider
            provider_config = config.get_provider_config(provider)
            model = provider_config.get("default_model", "gpt-4o-mini") if provider_config else "gpt-4o-mini"
        
        return provider.strip().lower(), model.strip()
    
    @staticmethod
    def _validate_provider_model(provider: str, model: str) -> bool:
        """
        Validate if the provider and model combination is supported (internal helper).
        
        Args:
            provider: LLM provider name
            model: Model name
            
        Returns:
            True if valid, False otherwise
        """
        config = get_llm_config()
        
        if not config.is_provider_supported(provider):
            logger.warning(f"Unsupported provider: {provider}")
            return False
        
        provider_config = config.get_provider_config(provider)
        if not provider_config:
            return False
            
        supported_models = provider_config["models"]
        if model not in supported_models:
            logger.warning(
                f"Model {model} not in supported models for {provider}: {supported_models}"
            )
            return False
        
        return True
    
    @staticmethod
    def create_llm(
        llm_config: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> BaseChatModel:
        """
        Create an LLM instance based on configuration.
        
        Args:
            llm_config: LLM configuration string (e.g., "openai:gpt-4o-mini")
            temperature: Temperature for generation (0.0 - 1.0)
            max_tokens: Maximum tokens to generate (optional)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Initialized LLM instance
            
        Raises:
            ValueError: If provider is not supported or API key is missing
            
        Examples:
            >>> llm = LLMFactory.create_llm("openai:gpt-4o-mini", temperature=0.3)
            >>> llm = LLMFactory.create_llm("anthropic:claude-3-5-sonnet-20241022", temperature=0.5)
            >>> llm = LLMFactory.create_llm("google:gemini-1.5-flash", temperature=0.7)
        """
        config = get_llm_config()
        provider, model = LLMFactory._parse_llm_config(llm_config)
        
        # Validate configuration
        if not LLMFactory._validate_provider_model(provider, model):
            logger.warning(
                f"Invalid provider/model combination: {provider}:{model}. "
                f"Falling back to default: openai:gpt-4o-mini"
            )
            provider = "openai"
            model = "gpt-4o-mini"
        
        logger.info(f"Creating LLM instance: {provider}:{model} (temperature={temperature})")
        
        # Get LangSmith callbacks if tracing is enabled
        callbacks = get_langsmith_callbacks() if settings.LANGCHAIN_TRACING_V2 else None
        
        # Add metadata for tracing
        metadata = {
            "provider": provider,
            "model": model,
            "temperature": temperature,
        }
        if max_tokens:
            metadata["max_tokens"] = max_tokens
        
        # Create LLM based on provider
        if provider == "openai":
            if not config.OPENAI_API_KEY:
                raise ValueError(
                    "OPENAI_API_KEY not found in environment variables. "
                    "Please set it to use OpenAI models."
                )
            
            llm_params = {
                "model": model,
                "temperature": temperature,
                "api_key": config.OPENAI_API_KEY,
                "metadata": metadata,
            }
            if max_tokens:
                llm_params["max_tokens"] = max_tokens
            if callbacks:
                llm_params["callbacks"] = callbacks
            llm_params.update(kwargs)
            
            return ChatOpenAI(**llm_params)
        
        elif provider == "anthropic":
            if not config.ANTHROPIC_API_KEY:
                raise ValueError(
                    "ANTHROPIC_API_KEY not found in environment variables. "
                    "Please set it to use Anthropic models."
                )
            
            llm_params = {
                "model": model,
                "temperature": temperature,
                "api_key": config.ANTHROPIC_API_KEY,
                "metadata": metadata,
            }
            if max_tokens:
                llm_params["max_tokens"] = max_tokens
            if callbacks:
                llm_params["callbacks"] = callbacks
            llm_params.update(kwargs)
            
            return ChatAnthropic(**llm_params)
        
        elif provider == "google":
            if not config.GOOGLE_API_KEY:
                raise ValueError(
                    "GOOGLE_API_KEY not found in environment variables. "
                    "Please set it to use Google Gemini models."
                )
            
            llm_params = {
                "model": model,
                "temperature": temperature,
                "google_api_key": config.GOOGLE_API_KEY,
                "metadata": metadata,
            }
            if max_tokens:
                llm_params["max_output_tokens"] = max_tokens
            if callbacks:
                llm_params["callbacks"] = callbacks
            llm_params.update(kwargs)
            
            return ChatGoogleGenerativeAI(**llm_params)
        
        else:
            raise ValueError(
                f"Unsupported LLM provider: {provider}. "
                f"Supported providers: {config.get_available_providers()}"
            )
    
    @staticmethod
    def get_available_providers() -> dict:
        """
        Get all available providers and their models.
        
        Returns:
            Dictionary of providers with their supported models
        """
        config = get_llm_config()
        return config.SUPPORTED_PROVIDERS


# Convenience function for quick access
def get_llm(llm_config: str, temperature: float = 0.7, **kwargs) -> BaseChatModel:
    """
    Convenience function to create an LLM instance.
    
    Args:
        llm_config: LLM configuration string (e.g., "openai:gpt-4o-mini")
        temperature: Temperature for generation
        **kwargs: Additional provider-specific parameters
        
    Returns:
        Initialized LLM instance
    """
    return LLMFactory.create_llm(llm_config, temperature, **kwargs)
