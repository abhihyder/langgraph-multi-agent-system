"""
Handler Layer Module

Provides specialized request processors for different request types:
- BaseHandler: Abstract base class for all handlers
- SingleChatHandler: Text-based AI chat processing
- VoiceHandler: Audio input/output processing (STT/TTS)
- ThirdPartyHandler: External service integrations (Email, SMS, Drive)

Usage:
    from app.handlers import SingleChatHandler, VoiceHandler, ThirdPartyHandler
    
    handler = SingleChatHandler()
    response = await handler.handle(request)
"""

from app.handlers.base_handler import BaseHandler
from app.handlers.singlechat_handler import SingleChatHandler
from app.handlers.voice_handler import VoiceHandler
from app.handlers.third_party_handler import ThirdPartyHandler

__all__ = [
    "BaseHandler",
    "SingleChatHandler",
    "VoiceHandler",
    "ThirdPartyHandler",
]
