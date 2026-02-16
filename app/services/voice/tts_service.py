"""
Text-to-Speech (TTS) Service

Converts text to audio using OpenAI TTS API.

Features:
- Multiple voice options (alloy, echo, fable, onyx, nova, shimmer)
- Adjustable speech speed (0.25x - 4.0x)
- Multiple output formats (mp3, opus, aac, flac)
- Configurable quality (tts-1 or tts-1-hd)
- Streaming support for long texts
"""

from typing import Optional
import logging
import io
import time
from openai import OpenAI

from config.voice_config import get_voice_config
from .audio_processor import AudioProcessor
from .voice_models import SynthesisRequest, SynthesisResponse

logger = logging.getLogger(__name__)


class TTSService:
    """Text-to-Speech service using OpenAI TTS."""
    
    def __init__(self):
        """Initialize TTS service."""
        self.config = get_voice_config()
        self.client = OpenAI(api_key=self.config.openai_api_key)
        self.audio_processor = AudioProcessor()
        
        # Available voices
        self.available_voices = [
            "alloy",   # Neutral, balanced
            "echo",    # Male, clear
            "fable",   # British accent
            "onyx",    # Deep, authoritative
            "nova",    # Female, energetic
            "shimmer"  # Soft, soothing
        ]
        
        logger.info("TTSService initialized")
    
    async def synthesize(
        self,
        request: SynthesisRequest
    ) -> SynthesisResponse:
        """
        Convert text to speech.
        
        Args:
            request: SynthesisRequest with text to synthesize
            
        Returns:
            SynthesisResponse with audio data
            
        Raises:
            ValueError: If text invalid or voice unsupported
            Exception: For API errors
        """
        start_time = time.time()
        
        try:
            # Use configured voice if none specified
            voice = request.voice if request.voice else self.config.tts_voice
            
            # Validate voice
            if voice not in self.available_voices:
                raise ValueError(
                    f"Invalid voice '{voice}'. Choose from: {self.available_voices}"
                )
            
            # Use configured speed if none specified
            speed = request.speed if request.speed else self.config.tts_speed
            
            logger.info("Starting speech synthesis", extra={
                "text_length": len(request.text),
                "voice": voice,
                "speed": speed
            })
            
            # Call OpenAI TTS API
            response = self.client.audio.speech.create(
                model=self.config.tts_model,
                voice=voice,
                input=request.text,
                speed=speed,
                response_format=request.output_format
            )
            
            # Get audio bytes
            audio_bytes = response.content
            
            # Encode to base64
            import base64
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            processing_time = time.time() - start_time
            
            # Estimate duration (rough approximation: ~150 words per minute at 1.0 speed)
            word_count = len(request.text.split())
            estimated_duration = (word_count / 150.0) * 60.0 / speed
            
            logger.info("Speech synthesis completed", extra={
                "audio_size_kb": len(audio_bytes) / 1024,
                "estimated_duration": estimated_duration,
                "processing_time": processing_time
            })
            
            return SynthesisResponse(
                audio_data=audio_base64,
                audio_format=request.output_format,
                duration_seconds=round(estimated_duration, 2),
                character_count=len(request.text),
                metadata={
                    "voice": voice,
                    "speed": speed,
                    "model": self.config.tts_model,
                    "processing_time": round(processing_time, 3),
                    "audio_size_bytes": len(audio_bytes)
                }
            )
            
        except ValueError as e:
            logger.error(f"TTS validation error: {e}")
            raise
            
        except Exception as e:
            logger.error(f"TTS failed: {e}", exc_info=True)
            raise Exception(f"TTS service error: {str(e)}")
    
    async def synthesize_streaming(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0
    ):
        """
        Stream audio synthesis for long texts.
        
        Args:
            text: Text to synthesize
            voice: Voice ID
            speed: Speech speed
            
        Yields:
            Audio chunks
        """
        voice = voice if voice else self.config.tts_voice
        
        logger.info("Starting streaming synthesis")
        
        try:
            response = self.client.audio.speech.create(
                model=self.config.tts_model,
                voice=voice,
                input=text,
                speed=speed,
                response_format="mp3"
            )
            
            # Stream response
            yield response.content
            
        except Exception as e:
            logger.error(f"Streaming TTS failed: {e}", exc_info=True)
            raise
    
    def get_available_voices(self) -> list[dict]:
        """
        Get list of available voices with descriptions.
        
        Returns:
            List of voice info dicts
        """
        return [
            {
                "id": "alloy",
                "name": "Alloy",
                "description": "Neutral and balanced voice",
                "gender": "neutral"
            },
            {
                "id": "echo",
                "name": "Echo",
                "description": "Male voice, clear and professional",
                "gender": "male"
            },
            {
                "id": "fable",
                "name": "Fable",
                "description": "British accent, storytelling quality",
                "gender": "neutral"
            },
            {
                "id": "onyx",
                "name": "Onyx",
                "description": "Deep, authoritative male voice",
                "gender": "male"
            },
            {
                "id": "nova",
                "name": "Nova",
                "description": "Energetic female voice",
                "gender": "female"
            },
            {
                "id": "shimmer",
                "name": "Shimmer",
                "description": "Soft, soothing female voice",
                "gender": "female"
            }
        ]
