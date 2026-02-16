"""
Custom Exception Classes for Multi-Agent System

Organized exceptions following SOLID principles:
- NodeError: Agent graph node execution errors
- GraphError: Graph-level errors  
- ServiceError: External service integration errors
- ValidationError: Input/data validation errors
- AuthenticationError: Authentication and authorization errors
"""

from typing import Optional, Any


# ========== Graph & Node Exceptions ==========

class NodeError(Exception):
    """Custom exception for node execution errors"""
    def __init__(
        self, 
        message: str, 
        node_name: str, 
        node_type: str, 
        original_error: Optional[Exception] = None
    ):
        self.message = message
        self.node_name = node_name
        self.node_type = node_type
        self.original_error = original_error
        super().__init__(self.message)
    
    def __str__(self):
        base = f"[{self.node_type}:{self.node_name}] {self.message}"
        if self.original_error:
            base += f" (Caused by: {str(self.original_error)})"
        return base


class GraphError(Exception):
    """Exception for graph-level errors"""
    def __init__(self, message: str, graph_name: str, original_error: Optional[Exception] = None):
        self.message = message
        self.graph_name = graph_name
        self.original_error = original_error
        super().__init__(self.message)
    
    def __str__(self):
        base = f"[Graph:{self.graph_name}] {self.message}"
        if self.original_error:
            base += f" (Caused by: {str(self.original_error)})"
        return base


class GraphNotBuiltError(GraphError):
    """Exception when graph is used before being built"""
    def __init__(self, graph_name: str):
        super().__init__(
            f"Graph not built. Call build_graph() first.",
            graph_name
        )


# ========== Service & Integration Exceptions ==========

class ServiceError(Exception):
    """Base exception for external service errors"""
    def __init__(self, message: str, service_name: str, original_error: Optional[Exception] = None):
        self.message = message
        self.service_name = service_name
        self.original_error = original_error
        super().__init__(self.message)
    
    def __str__(self):
        base = f"[Service:{self.service_name}] {self.message}"
        if self.original_error:
            base += f" (Caused by: {str(self.original_error)})"
        return base


class EmailServiceError(ServiceError):
    """Exception for Gmail/Email service errors"""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message, "Email", original_error)


class AuthenticationServiceError(ServiceError):
    """Exception for authentication errors"""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message, "Authentication", original_error)


class VoiceServiceError(ServiceError):
    """Exception for voice service errors (TTS/STT)"""
    def __init__(self, message: str, service_type: str = "Voice", original_error: Optional[Exception] = None):
        super().__init__(message, service_type, original_error)


class LLMServiceError(ServiceError):
    """Exception for LLM service errors"""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message, "LLM", original_error)


# ========== Validation Exceptions ==========

class ValidationError(Exception):
    """Base exception for validation errors"""
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)
    
    def __str__(self):
        base = self.message
        if self.field:
            base = f"[Field:{self.field}] {base}"
        if self.value is not None:
            base += f" (Value: {self.value})"
        return base


class ParameterValidationError(ValidationError):
    """Exception for parameter validation errors"""
    pass


class EmailValidationError(ValidationError):
    """Exception for email validation errors"""
    def __init__(self, message: str, email: Optional[str] = None):
        super().__init__(message, field="email", value=email)


class AudioValidationError(ValidationError):
    """Exception for audio format/data validation errors"""
    pass


# ========== Authentication & Authorization Exceptions ==========

class AuthenticationError(Exception):
    """Base exception for authentication errors"""
    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def __str__(self):
        base = self.message
        if self.details:
            base += f" ({self.details})"
        return base


class NotAuthenticatedError(AuthenticationError):
    """Exception when service is not authenticated"""
    def __init__(self, service_name: str):
        super().__init__(
            f"{service_name} service not authenticated",
            details="Please authenticate before using this service"
        )


class GoogleAuthError(AuthenticationError):
    """Exception for Google OAuth errors"""
    pass


# ========== Configuration Exceptions ==========

class ConfigurationError(Exception):
    """Exception for configuration errors"""
    def __init__(self, message: str, config_key: Optional[str] = None):
        self.message = message
        self.config_key = config_key
        super().__init__(self.message)
    
    def __str__(self):
        base = self.message
        if self.config_key:
            base = f"[Config:{self.config_key}] {base}"
        return base


class MissingConfigError(ConfigurationError):
    """Exception for missing required configuration"""
    pass


class InvalidConfigError(ConfigurationError):
    """Exception for invalid configuration values"""
    pass


# ========== Export all exceptions ==========

__all__ = [
    # Graph & Node
    "NodeError",
    "GraphError",
    "GraphNotBuiltError",
    
    # Services
    "ServiceError",
    "EmailServiceError",
    "AuthenticationServiceError",
    "VoiceServiceError",
    "LLMServiceError",
    
    # Validation
    "ValidationError",
    "ParameterValidationError",
    "EmailValidationError",
    "AudioValidationError",
    
    # Authentication
    "AuthenticationError",
    "NotAuthenticatedError",
    "GoogleAuthError",
    
    # Configuration
    "ConfigurationError",
    "MissingConfigError",
    "InvalidConfigError",
]
