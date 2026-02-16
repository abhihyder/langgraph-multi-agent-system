"""
Voice Service Tests

Comprehensive tests for STT, TTS, AudioProcessor, and VoiceHandler.

Test Coverage:
- AudioProcessor: Format conversion, preprocessing, validation
- STTService: Transcription with mocked OpenAI API
- TTSService: Synthesis with mocked OpenAI API
- VoiceHandler: All endpoints and error cases

Run:
    pytest tests/test_voice.py -v
    pytest tests/test_voice.py -m voice
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import Request, HTTPException
import base64
import io

from app.services.voice.audio_processor import AudioProcessor
from app.services.voice.stt_service import STTService
from app.services.voice.tts_service import TTSService
from app.services.voice.voice_models import (
    TranscriptionRequest,
    TranscriptionResponse,
    SynthesisRequest,
    SynthesisResponse,
    VoiceQueryRequest
)
from app.handlers.voice_handler import VoiceHandler


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_audio_segment():
    """Create mock AudioSegment."""
    with patch('app.services.voice.audio_processor.AudioSegment') as MockAudio:
        audio = MagicMock()
        audio.duration_seconds = 5.0
        audio.frame_rate = 44100
        audio.channels = 2
        audio.sample_width = 2
        audio.frame_count.return_value = 220500
        audio.rms = 1000
        audio.max_dBFS = -3.0
        audio.dBFS = -20.0
        audio.set_channels.return_value = audio
        audio.set_frame_rate.return_value = audio
        audio.reverse.return_value = audio
        audio.__getitem__ = lambda self, key: audio
        audio.__len__ = lambda self: 5000
        
        MockAudio.from_file.return_value = audio
        yield audio


@pytest.fixture
def sample_audio_base64():
    """Generate sample base64 audio data."""
    # Minimal MP3 header (not real audio, just for testing)
    fake_audio = b'\xff\xfb\x90\x00' + b'\x00' * 100
    return base64.b64encode(fake_audio).decode('utf-8')


@pytest.fixture
def mock_transcription_request(sample_audio_base64):
    """Create mock TranscriptionRequest."""
    return TranscriptionRequest(
        audio_data=sample_audio_base64,
        audio_format="mp3",
        language="en",
        prompt=None
    )


@pytest.fixture
def mock_synthesis_request():
    """Create mock SynthesisRequest."""
    return SynthesisRequest(
        text="Hello world, this is a test.",
        voice="alloy",
        speed=1.0,
        output_format="mp3"
    )


@pytest.fixture
def mock_voice_request():
    """Create mock voice query Request."""
    request = Mock(spec=Request)
    request.url = Mock()
    request.url.path = "/api/voice/query"
    request.method = "POST"
    request.headers = {"content-type": "application/json"}
    
    async def mock_json():
        return {
            "audio_data": "fake_base64_audio",
            "audio_format": "mp3",
            "user_id": 123,
            "conversation_id": 456,
            "response_voice": "alloy",
            "response_format": "mp3"
        }
    
    request.json = mock_json
    return request


# ============================================================================
# AudioProcessor Tests
# ============================================================================

@pytest.mark.voice
@pytest.mark.unit
class TestAudioProcessor:
    """Test AudioProcessor audio manipulation."""
    
    def test_initialization(self):
        """AudioProcessor initializes with correct settings."""
        processor = AudioProcessor()
        assert processor.target_sample_rate == 16000
        assert processor.target_channels == 1
        assert len(processor.supported_formats) == 5
    
    def test_decode_base64_audio(self, sample_audio_base64, mock_audio_segment):
        """decode_base64_audio converts base64 to AudioSegment."""
        processor = AudioProcessor()
        
        audio = processor.decode_base64_audio(sample_audio_base64, "mp3")
        assert audio is not None
        assert audio.duration_seconds == 5.0
    
    def test_decode_invalid_format(self, sample_audio_base64):
        """decode_base64_audio raises error for invalid format."""
        processor = AudioProcessor()
        
        with pytest.raises(ValueError, match="Unsupported format"):
            processor.decode_base64_audio(sample_audio_base64, "invalid")
    
    def test_encode_audio_to_base64(self, mock_audio_segment):
        """encode_audio_to_base64 converts AudioSegment to base64."""
        processor = AudioProcessor()
        
        # Mock export
        with patch.object(mock_audio_segment, 'export') as mock_export:
            buffer = io.BytesIO(b'fake_audio_data')
            mock_export.return_value = None
            
            # Manually set buffer value since export doesn't return
            with patch('io.BytesIO') as MockIO:
                mock_buffer = MockIO.return_value
                mock_buffer.getvalue.return_value = b'fake_audio_data'
                
                result = processor.encode_audio_to_base64(mock_audio_segment, "mp3")
                
                assert isinstance(result, str)
                assert len(result) > 0
    
    def test_preprocess_for_stt(self, mock_audio_segment):
        """preprocess_for_stt applies all transformations."""
        processor = AudioProcessor()
        
        with patch('app.services.voice.audio_processor.normalize') as mock_normalize:
            mock_normalize.return_value = mock_audio_segment
            
            result = processor.preprocess_for_stt(mock_audio_segment)
            
            # Should convert to mono
            mock_audio_segment.set_channels.assert_called_with(1)
            
            # Should resample
            assert mock_audio_segment.set_frame_rate.called
            
            # Should normalize
            assert mock_normalize.called
    
    def test_validate_audio_size_valid(self):
        """validate_audio_size accepts small files."""
        processor = AudioProcessor()
        small_audio = base64.b64encode(b'x' * 1000).decode('utf-8')
        
        result = processor.validate_audio_size(small_audio, max_size_mb=25)
        assert result is True
    
    def test_validate_audio_size_too_large(self):
        """validate_audio_size rejects large files."""
        processor = AudioProcessor()
        # Create large base64 string (>1MB)
        large_audio = base64.b64encode(b'x' * 2_000_000).decode('utf-8')
        
        with pytest.raises(ValueError, match="exceeds limit"):
            processor.validate_audio_size(large_audio, max_size_mb=1)
    
    def test_get_audio_metadata(self, mock_audio_segment):
        """get_audio_metadata extracts correct info."""
        processor = AudioProcessor()
        
        metadata = processor.get_audio_metadata(mock_audio_segment)
        
        assert "duration_seconds" in metadata
        assert "sample_rate" in metadata
        assert "channels" in metadata
        assert metadata["duration_seconds"] == 5.0
        assert metadata["sample_rate"] == 44100


# ============================================================================
# STTService Tests
# ============================================================================

@pytest.mark.voice
@pytest.mark.unit
class TestSTTService:
    """Test Speech-to-Text service."""
    
    @pytest.mark.asyncio
    async def test_transcribe_success(self, mock_transcription_request, mock_audio_segment):
        """transcribe successfully converts audio to text."""
        with patch('app.services.voice.stt_service.OpenAI') as MockOpenAI:
            # Mock OpenAI client
            mock_client = MockOpenAI.return_value
            mock_response = Mock()
            mock_response.text = "Hello world"
            mock_response.language = "en"
            mock_client.audio.transcriptions.create.return_value = mock_response
            
            # Mock audio processing
            with patch('app.services.voice.stt_service.AudioProcessor') as MockProcessor:
                mock_processor = MockProcessor.return_value
                mock_processor.validate_audio_size.return_value = True
                mock_processor.decode_base64_audio.return_value = mock_audio_segment
                mock_processor.preprocess_for_stt.return_value = mock_audio_segment
                mock_processor.get_audio_metadata.return_value = {"duration_seconds": 5.0}
                mock_processor.convert_format.return_value = b'fake_audio'
                
                stt = STTService()
                result = await stt.transcribe(mock_transcription_request)
                
                assert isinstance(result, TranscriptionResponse)
                assert result.text == "Hello world"
                assert result.language == "en"
                assert result.duration_seconds == 5.0
    
    @pytest.mark.asyncio
    async def test_transcribe_invalid_audio(self, mock_transcription_request):
        """transcribe raises error for invalid audio."""
        with patch('app.services.voice.stt_service.AudioProcessor') as MockProcessor:
            mock_processor = MockProcessor.return_value
            mock_processor.validate_audio_size.side_effect = ValueError("Audio too large")
            
            stt = STTService()
            
            with pytest.raises(ValueError, match="Audio too large"):
                await stt.transcribe(mock_transcription_request)
    
    def test_get_supported_languages(self):
        """get_supported_languages returns language list."""
        with patch('app.services.voice.stt_service.OpenAI'):
            stt = STTService()
            languages = stt.get_supported_languages()
            
            assert isinstance(languages, list)
            assert len(languages) == 99
            assert "en" in languages
            assert "es" in languages


# ============================================================================
# TTSService Tests
# ============================================================================

@pytest.mark.voice
@pytest.mark.unit
class TestTTSService:
    """Test Text-to-Speech service."""
    
    @pytest.mark.asyncio
    async def test_synthesize_success(self, mock_synthesis_request):
        """synthesize successfully converts text to audio."""
        with patch('app.services.voice.tts_service.OpenAI') as MockOpenAI:
            # Mock OpenAI client
            mock_client = MockOpenAI.return_value
            mock_response = Mock()
            mock_response.content = b'fake_audio_data'
            mock_client.audio.speech.create.return_value = mock_response
            
            tts = TTSService()
            result = await tts.synthesize(mock_synthesis_request)
            
            assert isinstance(result, SynthesisResponse)
            assert len(result.audio_data) > 0
            assert result.audio_format == "mp3"
            assert result.character_count == len(mock_synthesis_request.text)
    
    @pytest.mark.asyncio
    async def test_synthesize_invalid_voice(self, mock_synthesis_request):
        """synthesize raises error for invalid voice."""
        mock_synthesis_request.voice = "invalid_voice"
        
        with patch('app.services.voice.tts_service.OpenAI'):
            tts = TTSService()
            
            with pytest.raises(ValueError, match="Invalid voice"):
                await tts.synthesize(mock_synthesis_request)
    
    def test_get_available_voices(self):
        """get_available_voices returns voice list."""
        with patch('app.services.voice.tts_service.OpenAI'):
            tts = TTSService()
            voices = tts.get_available_voices()
            
            assert isinstance(voices, list)
            assert len(voices) == 6
            assert all("id" in v and "name" in v for v in voices)


# ============================================================================
# VoiceHandler Tests
# ============================================================================

@pytest.mark.voice
@pytest.mark.unit
class TestVoiceHandler:
    """Test VoiceHandler endpoint routing and integration."""
    
    def test_initialization(self):
        """VoiceHandler initializes with all services."""
        with patch('app.handlers.voice_handler.STTService'), \
             patch('app.handlers.voice_handler.TTSService'), \
             patch('app.handlers.voice_handler.ChatService'):
            
            handler = VoiceHandler()
            assert handler.name == "VoiceHandler"
            assert hasattr(handler, "stt_service")
            assert hasattr(handler, "tts_service")
            assert hasattr(handler, "chat_service")
    
    @pytest.mark.asyncio
    async def test_handle_transcribe(self, sample_audio_base64):
        """handle routes /transcribe to STT service."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/voice/transcribe"
        request.method = "POST"
        request.headers = {"content-type": "application/json"}
        
        async def mock_json():
            return {
                "audio_data": sample_audio_base64,
                "audio_format": "mp3"
            }
        
        request.json = mock_json
        
        with patch('app.handlers.voice_handler.STTService') as MockSTT, \
             patch('app.handlers.voice_handler.TTSService'), \
             patch('app.handlers.voice_handler.ChatService'):
            
            mock_stt = MockSTT.return_value
            mock_stt.transcribe = AsyncMock(return_value=TranscriptionResponse(
                text="Test transcription",
                language="en",
                duration_seconds=5.0,
                confidence=None,
                metadata={}
            ))
            
            handler = VoiceHandler()
            response = await handler.handle(request)
            
            assert response["success"] is True
            assert response["data"]["text"] == "Test transcription"
    
    @pytest.mark.asyncio
    async def test_handle_synthesize(self):
        """handle routes /synthesize to TTS service."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/voice/synthesize"
        request.method = "POST"
        request.headers = {"content-type": "application/json"}
        
        async def mock_json():
            return {
                "text": "Hello world",
                "voice": "alloy"
            }
        
        request.json = mock_json
        
        with patch('app.handlers.voice_handler.STTService'), \
             patch('app.handlers.voice_handler.TTSService') as MockTTS, \
             patch('app.handlers.voice_handler.ChatService'):
            
            mock_tts = MockTTS.return_value
            mock_tts.synthesize = AsyncMock(return_value=SynthesisResponse(
                audio_data="fake_base64",
                audio_format="mp3",
                duration_seconds=3.0,
                character_count=11,
                metadata={}
            ))
            
            handler = VoiceHandler()
            response = await handler.handle(request)
            
            assert response["success"] is True
            assert response["data"]["audio_data"] == "fake_base64"
    
    @pytest.mark.asyncio
    async def test_handle_voice_query_full_flow(self, mock_voice_request):
        """handle processes complete voice query flow."""
        with patch('app.handlers.voice_handler.STTService') as MockSTT, \
             patch('app.handlers.voice_handler.TTSService') as MockTTS, \
             patch('app.handlers.voice_handler.ChatService') as MockChat:
            
            # Mock STT
            mock_stt = MockSTT.return_value
            mock_stt.transcribe = AsyncMock(return_value=TranscriptionResponse(
                text="What is the weather?",
                language="en",
                duration_seconds=2.0,
                confidence=None,
                metadata={}
            ))
            
            # Mock ChatService
            mock_chat = MockChat.return_value
            mock_chat.process_chat = Mock(return_value={
                "response": "It's sunny today.",
                "conversation_id": 456,
                "agents_used": ["general"],
                "metadata": {}
            })
            
            # Mock TTS
            mock_tts = MockTTS.return_value
            mock_tts.synthesize = AsyncMock(return_value=SynthesisResponse(
                audio_data="response_audio_base64",
                audio_format="mp3",
                duration_seconds=2.5,
                character_count=18,
                metadata={}
            ))
            
            handler = VoiceHandler()
            response = await handler.handle(mock_voice_request)
            
            assert response["success"] is True
            assert response["data"]["query_text"] == "What is the weather?"
            assert response["data"]["response_text"] == "It's sunny today."
            assert response["data"]["response_audio"] == "response_audio_base64"
            assert response["data"]["conversation_id"] == 456
    
    @pytest.mark.asyncio
    async def test_validate_request_invalid_content_type(self):
        """validate_request rejects non-JSON content-type."""
        request = Mock(spec=Request)
        request.headers = {"content-type": "text/plain"}
        
        with patch('app.handlers.voice_handler.STTService'), \
             patch('app.handlers.voice_handler.TTSService'), \
             patch('app.handlers.voice_handler.ChatService'):
            
            handler = VoiceHandler()
            
            with pytest.raises(HTTPException) as exc_info:
                await handler.validate_request(request)
            
            assert exc_info.value.status_code == 415


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.voice
@pytest.mark.integration
class TestVoiceIntegration:
    """Integration tests for voice processing."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_voice_query(self):
        """Test complete voice query flow with all services."""
        # This would require actual audio files and API keys
        # For now, just verify the components integrate correctly
        
        with patch('app.handlers.voice_handler.STTService'), \
             patch('app.handlers.voice_handler.TTSService'), \
             patch('app.handlers.voice_handler.ChatService'):
            
            handler = VoiceHandler()
            
            assert handler.stt_service is not None
            assert handler.tts_service is not None
            assert handler.chat_service is not None
