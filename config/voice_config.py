"""
Voice Processing Configuration

Configuration for Speech-to-Text and Text-to-Speech services.

Environment Variables Required:
- OPENAI_API_KEY: For Whisper STT and OpenAI TTS
- ELEVENLABS_API_KEY: Optional, for ElevenLabs TTS (higher quality)
- VOICE_MODEL: whisper-1 (default) or other models
- TTS_VOICE: alloy, echo, fable, onyx, nova, shimmer
"""

from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class VoiceConfig(BaseSettings):
    """Voice processing configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="VOICE_",
        case_sensitive=False
    )
    
    # API Keys
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    elevenlabs_api_key: Optional[str] = os.getenv("ELEVENLABS_API_KEY")
    
    # STT Configuration
    stt_provider: Literal["openai", "google"] = "openai"
    stt_model: str = "whisper-1"
    stt_language: Optional[str] = None  # Auto-detect by default
    stt_temperature: float = 0.0  # 0.0-1.0, higher = more creative
    
    # TTS Configuration
    tts_provider: Literal["openai", "elevenlabs"] = "openai"
    tts_model: str = "tts-1"  # tts-1 or tts-1-hd (higher quality)
    tts_voice: str = "alloy"  # alloy, echo, fable, onyx, nova, shimmer
    tts_speed: float = 1.0  # 0.25-4.0
    
    # Audio Processing
    supported_formats: list[str] = ["mp3", "wav", "m4a", "webm", "ogg"]
    max_audio_size_mb: int = 25  # OpenAI Whisper limit
    default_sample_rate: int = 16000  # 16kHz for Whisper
    default_channels: int = 1  # Mono
    
    # Response Caching
    enable_cache: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour
    
    # Timeouts
    stt_timeout_seconds: int = 60
    tts_timeout_seconds: int = 30


# Global instance
voice_config = VoiceConfig()


def get_voice_config() -> VoiceConfig:
    """Get voice configuration instance."""
    return voice_config
