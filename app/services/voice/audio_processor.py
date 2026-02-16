"""
Audio Processor

Handles audio file format conversions, preprocessing, and validation.

Features:
- Format conversion (mp3, wav, m4a, webm, ogg)
- Audio preprocessing (normalize volume, remove silence)
- Sample rate conversion
- Channel conversion (stereo to mono)
- Audio validation and metadata extraction
"""

from typing import Optional, Tuple, BinaryIO
from pydub import AudioSegment
from pydub.effects import normalize
import io
import logging
import base64

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Process audio files for STT/TTS operations."""
    
    def __init__(self):
        """Initialize audio processor."""
        self.supported_formats = ["mp3", "wav", "m4a", "webm", "ogg"]
        self.target_sample_rate = 16000  # 16kHz for Whisper
        self.target_channels = 1  # Mono
    
    def decode_base64_audio(self, audio_data: str, audio_format: str) -> AudioSegment:
        """
        Decode base64 audio data to AudioSegment.
        
        Args:
            audio_data: Base64-encoded audio
            audio_format: Audio format (mp3, wav, etc.)
            
        Returns:
            AudioSegment object
            
        Raises:
            ValueError: If format unsupported or decoding fails
        """
        if audio_format not in self.supported_formats:
            raise ValueError(f"Unsupported format: {audio_format}")
        
        try:
            # Decode base64
            audio_bytes = base64.b64decode(audio_data)
            
            # Load audio from bytes
            audio = AudioSegment.from_file(
                io.BytesIO(audio_bytes),
                format=audio_format
            )
            
            logger.info(f"Decoded audio: {audio_format}, duration={audio.duration_seconds}s")
            return audio
            
        except Exception as e:
            logger.error(f"Failed to decode audio: {e}")
            raise ValueError(f"Audio decoding failed: {str(e)}")
    
    def encode_audio_to_base64(self, audio: AudioSegment, output_format: str) -> str:
        """
        Encode AudioSegment to base64 string.
        
        Args:
            audio: AudioSegment object
            output_format: Output format (mp3, wav, etc.)
            
        Returns:
            Base64-encoded audio string
        """
        buffer = io.BytesIO()
        audio.export(buffer, format=output_format)
        audio_bytes = buffer.getvalue()
        
        return base64.b64encode(audio_bytes).decode('utf-8')
    
    def preprocess_for_stt(self, audio: AudioSegment) -> AudioSegment:
        """
        Preprocess audio for speech-to-text.
        
        Operations:
        - Convert to mono
        - Resample to 16kHz
        - Normalize volume
        - Remove leading/trailing silence
        
        Args:
            audio: Input AudioSegment
            
        Returns:
            Preprocessed AudioSegment
        """
        # Convert to mono
        if audio.channels > 1:
            audio = audio.set_channels(self.target_channels)
            logger.debug("Converted to mono")
        
        # Resample to target rate
        if audio.frame_rate != self.target_sample_rate:
            audio = audio.set_frame_rate(self.target_sample_rate)
            logger.debug(f"Resampled to {self.target_sample_rate}Hz")
        
        # Normalize volume
        audio = normalize(audio)
        logger.debug("Normalized volume")
        
        # Remove silence
        audio = self._remove_silence(audio)
        
        return audio
    
    def _remove_silence(
        self,
        audio: AudioSegment,
        silence_thresh: int = -40,
        chunk_size: int = 10
    ) -> AudioSegment:
        """
        Remove leading and trailing silence.
        
        Args:
            audio: Input audio
            silence_thresh: Silence threshold in dBFS (default -40)
            chunk_size: Chunk size in milliseconds (default 10ms)
            
        Returns:
            Audio with silence removed
        """
        def detect_leading_silence(sound, silence_threshold=-40.0, chunk_size=10):
            trim_ms = 0
            assert chunk_size > 0
            while sound[trim_ms:trim_ms+chunk_size].dBFS < silence_threshold and trim_ms < len(sound):
                trim_ms += chunk_size
            return trim_ms
        
        start_trim = detect_leading_silence(audio, silence_thresh, chunk_size)
        end_trim = detect_leading_silence(audio.reverse(), silence_thresh, chunk_size)
        
        duration = len(audio)
        trimmed: AudioSegment = audio[start_trim:duration-end_trim]  # type: ignore[assignment]
        
        logger.debug(f"Removed {start_trim + end_trim}ms silence")
        return trimmed
    
    def convert_format(
        self,
        audio: AudioSegment,
        target_format: str
    ) -> bytes:
        """
        Convert audio to target format.
        
        Args:
            audio: Input AudioSegment
            target_format: Target format (mp3, wav, etc.)
            
        Returns:
            Audio bytes in target format
        """
        if target_format not in self.supported_formats:
            raise ValueError(f"Unsupported target format: {target_format}")
        
        buffer = io.BytesIO()
        audio.export(buffer, format=target_format)
        
        logger.info(f"Converted audio to {target_format}")
        return buffer.getvalue()
    
    def get_audio_metadata(self, audio: AudioSegment) -> dict:
        """
        Extract audio metadata.
        
        Args:
            audio: AudioSegment object
            
        Returns:
            Dict with metadata (duration, sample_rate, channels, etc.)
        """
        return {
            "duration_seconds": audio.duration_seconds,
            "sample_rate": audio.frame_rate,
            "channels": audio.channels,
            "sample_width": audio.sample_width,
            "frame_count": audio.frame_count(),
            "rms": audio.rms,
            "max_dBFS": audio.max_dBFS,
            "dBFS": audio.dBFS
        }
    
    def validate_audio_size(self, audio_data: str, max_size_mb: int = 25) -> bool:
        """
        Validate audio size is within limits.
        
        Args:
            audio_data: Base64-encoded audio
            max_size_mb: Maximum size in MB
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If audio exceeds size limit
        """
        # Calculate size from base64 (base64 adds ~33% overhead)
        size_bytes = len(audio_data) * 3 / 4
        size_mb = size_bytes / (1024 * 1024)
        
        if size_mb > max_size_mb:
            raise ValueError(
                f"Audio size ({size_mb:.2f}MB) exceeds limit ({max_size_mb}MB)"
            )
        
        logger.debug(f"Audio size: {size_mb:.2f}MB")
        return True
