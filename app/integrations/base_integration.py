"""
Base Integration Class

Abstract base for all third-party service integrations (Gmail, SMS, Drive, etc).

Provides common interface and error handling patterns.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class IntegrationConfig:
    """Configuration for an integration"""
    name: str
    provider: str
    credentials: Dict[str, Any]
    settings: Optional[Dict[str, Any]] = None


class BaseIntegration(ABC):
    """
    Abstract base class for third-party service integrations.
    
    All integrations (Gmail, SMS, Drive, etc.) should inherit from this class.
    """
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        """
        Initialize integration.
        
        Args:
            config: IntegrationConfig object for the service
        """
        if config:
            self.config = config.settings or {}
            self.credentials = config.credentials
            self.name = config.name
            self.provider = config.provider
        else:
            self.config = {}
            self.credentials = {}
            self.name = "unknown"
            self.provider = "unknown"
        self.is_authenticated = False
        logger.info(f"Initialized {self.__class__.__name__}")
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """
        Authenticate with the service.
        
        Args:
            credentials: Authentication credentials
            
        Returns:
            True if authentication successful
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if service is healthy and accessible.
        
        Returns:
            True if service is accessible
        """
        pass
    
    def get_service_name(self) -> str:
        """
        Get the name of the integration service.
        
        Returns:
            Service name
        """
        return self.__class__.__name__.replace("Service", "").replace("Integration", "")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the integration.
        
        Returns:
            Status dictionary with authentication and health info
        """
        return {
            "service": self.get_service_name(),
            "authenticated": self.is_authenticated,
            "config_loaded": bool(self.config),
        }
