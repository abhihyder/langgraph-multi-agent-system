"""
Voice Models - Pydantic Models for Voice Processing

Request/Response models for voice operations.
"""

from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
import base64


class TranscriptionRequest(BaseModel):
    """Request model for audio transcription (STT)."""
    
    audio_data: str = Field(
        ...,
        description="Base64-encoded audio data"
    )
    audio_format: str = Field(
        default="mp3",
        description="Audio format: mp3, wav, m4a, webm, ogg"
    )
    language: Optional[str] = Field(
        None,
        description="Language code (e.g., 'en', 'es'). Auto-detect if None"
    )
    prompt: Optional[str] = Field(
        None,
        description="Optional context to guide transcription"
    )
    
    @field_validator("audio_format")
    @classmethod
    def validate_format(cls, v):
        """Validate audio format."""
        supported = ["mp3", "wav", "m4a", "webm", "ogg"]
        if v.lower() not in supported:
            raise ValueError(f"Unsupported format. Use one of: {supported}")
        return v.lower()


class TranscriptionResponse(BaseModel):
    """Response model for audio transcription."""
    
    text: str = Field(..., description="Transcribed text")
    language: Optional[str] = Field(None, description="Detected language")
    duration_seconds: Optional[float] = Field(None, description="Audio duration")
    confidence: Optional[float] = Field(None, description="Transcription confidence (0-1)")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SynthesisRequest(BaseModel):
    """Request model for text-to-speech synthesis (TTS)."""
    
    text: str = Field(
        ...,
        description="Text to synthesize",
        max_length=4096
    )
    voice: Optional[str] = Field(
        None,
        description="Voice ID: alloy, echo, fable, onyx, nova, shimmer"
    )
    speed: Optional[float] = Field(
        1.0,
        ge=0.25,
        le=4.0,
        description="Speech speed (0.25-4.0)"
    )
    output_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = Field(
        default="mp3",
        description="Output audio format"
    )
    
    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        """Validate text is not empty."""
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()


class SynthesisResponse(BaseModel):
    """Response model for text-to-speech."""
    
    audio_data: str = Field(..., description="Base64-encoded audio data")
    audio_format: str = Field(..., description="Audio format")
    duration_seconds: Optional[float] = Field(None, description="Audio duration")
    character_count: int = Field(..., description="Number of characters synthesized")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VoiceQueryRequest(BaseModel):
    """Request model for voice query (STT + AI + TTS)."""
    
    audio_data: str = Field(..., description="Base64-encoded audio query")
    audio_format: str = Field(default="mp3", description="Input audio format")
    user_id: int = Field(..., description="User ID for context")
    conversation_id: Optional[int] = Field(None, description="Conversation ID")
    response_voice: Optional[str] = Field(None, description="Voice for response")
    response_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = Field(default="mp3", description="Output audio format")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class VoiceQueryResponse(BaseModel):
    """Response model for voice query."""
    
    # Text components
    query_text: str = Field(..., description="Transcribed query")
    response_text: str = Field(..., description="AI response text")
    
    # Audio components
    response_audio: str = Field(..., description="Base64-encoded response audio")
    audio_format: str = Field(..., description="Response audio format")
    
    # Metadata
    conversation_id: int = Field(..., description="Conversation ID")
    agents_used: list[str] = Field(default_factory=list, description="Agents invoked")
    processing_time: float = Field(..., description="Total processing time")
    metadata: Dict[str, Any] = Field(default_factory=dict)
