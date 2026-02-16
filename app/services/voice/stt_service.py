"""
Speech-to-Text (STT) Service

Converts audio to text using OpenAI Whisper API.

Features:
- Multiple audio format support (mp3, wav, m4a, webm, ogg)
- Automatic language detection
- Audio preprocessing (normalization, silence removal)
- Configurable models and parameters
- Error handling and retry logic
"""

from typing import Optional, Dict, Any
import logging
import io
import time
from openai import OpenAI
from pydub import AudioSegment

from config.voice_config import get_voice_config
from .audio_processor import AudioProcessor
from .voice_models import TranscriptionRequest, TranscriptionResponse

logger = logging.getLogger(__name__)


class STTService:
    """Speech-to-Text service using OpenAI Whisper."""
    
    def __init__(self):
        """Initialize STT service."""
        self.config = get_voice_config()
        self.client = OpenAI(api_key=self.config.openai_api_key)
        self.audio_processor = AudioProcessor()
        logger.info("STTService initialized")
    
    async def transcribe(
        self,
        request: TranscriptionRequest
    ) -> TranscriptionResponse:
        """
        Transcribe audio to text.
        
        Args:
            request: TranscriptionRequest with audio data
            
        Returns:
            TranscriptionResponse with transcribed text
            
        Raises:
            ValueError: If audio invalid or processing fails
            Exception: For API errors
        """
        start_time = time.time()
        
        try:
            logger.info("Starting transcription", extra={
                "format": request.audio_format,
                "language": request.language
            })
            
            # Validate audio size
            self.audio_processor.validate_audio_size(
                request.audio_data,
                self.config.max_audio_size_mb
            )
            
            # Decode and preprocess audio
            audio = self.audio_processor.decode_base64_audio(
                request.audio_data,
                request.audio_format
            )
            
            # Preprocess for optimal STT
            audio = self.audio_processor.preprocess_for_stt(audio)
            
            # Get audio metadata
            metadata = self.audio_processor.get_audio_metadata(audio)
            
            # Convert to format suitable for Whisper (mp3 or wav)
            audio_bytes = self.audio_processor.convert_format(audio, "mp3")
            
            # Create file-like object
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.mp3"
            
            # Call Whisper API
            logger.debug("Calling Whisper API")
            
            # Build parameters for API call
            api_params: dict = {
                "model": self.config.stt_model,
                "file": audio_file,
                "response_format": "verbose_json"
            }
            
            # Add optional parameters only if provided
            if request.language:
                api_params["language"] = request.language
            if request.prompt:
                api_params["prompt"] = request.prompt
            if self.config.stt_temperature > 0:
                api_params["temperature"] = self.config.stt_temperature
            
            response = self.client.audio.transcriptions.create(**api_params)  # type: ignore[arg-type]
            
            processing_time = time.time() - start_time
            
            logger.info("Transcription completed", extra={
                "text_length": len(response.text),
                "duration": metadata["duration_seconds"],
                "processing_time": processing_time
            })
            
            return TranscriptionResponse(
                text=response.text,
                language=response.language if hasattr(response, 'language') else request.language,
                duration_seconds=metadata["duration_seconds"],
                confidence=None,  # Whisper doesn't provide confidence
                metadata={
                    "processing_time": round(processing_time, 3),
                    "audio_metadata": metadata,
                    "model": self.config.stt_model
                }
            )
            
        except ValueError as e:
            logger.error(f"Transcription validation error: {e}")
            raise
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            raise Exception(f"STT service error: {str(e)}")
    
    def get_supported_languages(self) -> list[str]:
        """
        Get list of supported languages.
        
        Returns:
            List of ISO 639-1 language codes
        """
        # Whisper supports 99 languages
        return [
            "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr",
            "pl", "ca", "nl", "ar", "sv", "it", "id", "hi", "fi", "vi",
            "he", "uk", "el", "ms", "cs", "ro", "da", "hu", "ta", "no",
            "th", "ur", "hr", "bg", "lt", "la", "mi", "ml", "cy", "sk",
            "te", "fa", "lv", "bn", "sr", "az", "sl", "kn", "et", "mk",
            "br", "eu", "is", "hy", "ne", "mn", "bs", "kk", "sq", "sw",
            "gl", "mr", "pa", "si", "km", "sn", "yo", "so", "af", "oc",
            "ka", "be", "tg", "sd", "gu", "am", "yi", "lo", "uz", "fo",
            "ht", "ps", "tk", "nn", "mt", "sa", "lb", "my", "bo", "tl",
            "mg", "as", "tt", "haw", "ln", "ha", "ba", "jw", "su"
        ]
