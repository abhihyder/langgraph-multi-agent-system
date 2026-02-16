"""
Voice Services Package

Provides Speech-to-Text (STT) and Text-to-Speech (TTS) capabilities.

Components:
- STTService: Convert audio to text using OpenAI Whisper or Google Speech
- TTSService: Convert text to audio using OpenAI TTS or ElevenLabs
- AudioProcessor: Handle audio format conversions and preprocessing
- VoiceModels: Pydantic models for voice requests/responses

Usage:
    from app.services.voice import STTService, TTSService
    
    stt = STTService()
    text = await stt.transcribe(audio_file)
    
    tts = TTSService()
    audio = await tts.synthesize(text)
"""

from .stt_service import STTService
from .tts_service import TTSService
from .audio_processor import AudioProcessor
from .voice_models import (
    TranscriptionRequest,
    TranscriptionResponse,
    SynthesisRequest,
    SynthesisResponse,
    VoiceQueryRequest,
    VoiceQueryResponse
)

__all__ = [
    "STTService",
    "TTSService",
    "AudioProcessor",
    "TranscriptionRequest",
    "TranscriptionResponse",
    "SynthesisRequest",
    "SynthesisResponse",
    "VoiceQueryRequest",
    "VoiceQueryResponse"
]
