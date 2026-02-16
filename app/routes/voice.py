"""
Voice Routes - Voice Processing Endpoints

Provides voice interaction capabilities through STT and TTS.

Endpoints:
- POST /api/voice/transcribe - Convert audio to text
- POST /api/voice/synthesize - Convert text to audio
- POST /api/voice/query - Complete voice interaction flow

Architecture:
    Client → /api/voice/* → VoiceHandler → STT/TTS Services → Response
"""

from fastapi import APIRouter, Request
from typing import Dict, Any

from app.handlers.voice_handler import VoiceHandler

# Create router
router = APIRouter(prefix="/api/voice", tags=["voice"])

# Initialize handler
voice_handler = VoiceHandler()


@router.post("/transcribe")
async def transcribe_audio(request: Request) -> Dict[str, Any]:
    """
    Transcribe audio to text (Speech-to-Text).
    
    Request Body:
        {
            "audio_data": "base64_encoded_audio",
            "audio_format": "mp3",  # mp3, wav, m4a, webm, ogg
            "language": "en",  # optional, auto-detect if not provided
            "prompt": "optional context"  # optional, guides transcription
        }
    
    Response:
        {
            "success": true,
            "data": {
                "text": "transcribed text",
                "language": "en",
                "duration_seconds": 5.2,
                "confidence": null,
                "metadata": {...}
            },
            "handler": "VoiceHandler",
            "processing_time": 1.234
        }
    """
    return await voice_handler.handle(request)


@router.post("/synthesize")
async def synthesize_speech(request: Request) -> Dict[str, Any]:
    """
    Convert text to speech (Text-to-Speech).
    
    Request Body:
        {
            "text": "text to synthesize",
            "voice": "alloy",  # optional: alloy, echo, fable, onyx, nova, shimmer
            "speed": 1.0,  # optional: 0.25-4.0
            "output_format": "mp3"  # optional: mp3, opus, aac, flac
        }
    
    Response:
        {
            "success": true,
            "data": {
                "audio_data": "base64_encoded_audio",
                "audio_format": "mp3",
                "duration_seconds": 3.5,
                "character_count": 150,
                "metadata": {...}
            },
            "handler": "VoiceHandler",
            "processing_time": 0.856
        }
    """
    return await voice_handler.handle(request)


@router.post("/query")
async def voice_query(request: Request) -> Dict[str, Any]:
    """
    Complete voice interaction: Audio Query → AI Response → Audio.
    
    Combines STT, AI processing, and TTS into one flow.
    
    Request Body:
        {
            "audio_data": "base64_encoded_audio",
            "audio_format": "mp3",
            "user_id": 123,
            "conversation_id": 456,  # optional
            "response_voice": "alloy",  # optional
            "response_format": "mp3",  # optional
            "context": {}  # optional
        }
    
    Response:
        {
            "success": true,
            "data": {
                "query_text": "transcribed query",
                "response_text": "AI response",
                "response_audio": "base64_encoded_audio",
                "audio_format": "mp3",
                "conversation_id": 456,
                "agents_used": ["general"],
                "processing_time": 3.456,
                "metadata": {...}
            },
            "handler": "VoiceHandler",
            "processing_time": 3.456
        }
    """
    return await voice_handler.handle(request)


@router.get("/voices")
async def get_available_voices() -> Dict[str, Any]:
    """
    Get list of available TTS voices.
    
    Response:
        {
            "voices": [
                {
                    "id": "alloy",
                    "name": "Alloy",
                    "description": "Neutral and balanced voice",
                    "gender": "neutral"
                },
                ...
            ]
        }
    """
    return {
        "voices": voice_handler.tts_service.get_available_voices()
    }


@router.get("/languages")
async def get_supported_languages() -> Dict[str, Any]:
    """
    Get list of supported languages for STT.
    
    Response:
        {
            "languages": ["en", "es", "fr", "de", ...],
            "count": 99
        }
    """
    languages = voice_handler.stt_service.get_supported_languages()
    return {
        "languages": languages,
        "count": len(languages)
    }
