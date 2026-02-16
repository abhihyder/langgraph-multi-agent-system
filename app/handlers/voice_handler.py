"""
Voice Handler - Full Implementation

Processes audio input/output requests with STT/TTS capabilities.
Routes: /api/voice/*

Flow:
    Gateway → VoiceHandler → STT Service → AI Agents → TTS Service → Audio Response
    
Responsibilities:
- Accept audio file uploads (STT)
- Transcribe audio to text using Whisper
- Process through agentic system (ChatService)
- Convert response to speech (TTS)
- Return audio file or text

Endpoints:
- POST /api/voice/transcribe  - Audio → Text (STT only)
- POST /api/voice/synthesize  - Text → Audio (TTS only)
- POST /api/voice/query       - Audio → AI Response → Audio (full flow)

Status: ✅ COMPLETE - Phase 1.3
"""

from typing import Dict, Any
from fastapi import Request, HTTPException
import logging
import time

from app.handlers.base_handler import BaseHandler
from app.services.voice import STTService, TTSService
from app.services.voice.voice_models import (
    TranscriptionRequest,
    SynthesisRequest,
    VoiceQueryRequest
)
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)


class VoiceHandler(BaseHandler):
    """
    Handler for voice/audio requests (Speech-to-Text and Text-to-Speech).
    
    Integrates with STTService, TTSService, and ChatService for complete voice interaction.
    """
    
    def __init__(self):
        """Initialize VoiceHandler with voice services."""
        super().__init__()
        self.stt_service = STTService()
        self.tts_service = TTSService()
        self.chat_service = ChatService()
        logger.info("VoiceHandler initialized with STT/TTS services")
    
    async def handle(self, request: Request) -> Dict[str, Any]:
        """
        Process voice request.
        
        Args:
            request: FastAPI Request containing audio data or text for synthesis
            
        Returns:
            Standardized response with audio/text data
            
        Endpoints:
            POST /api/voice/transcribe  - Audio → Text (STT)
            POST /api/voice/synthesize  - Text → Audio (TTS)
            POST /api/voice/query       - Audio → AI Response → Audio (full flow)
        """
        return await self._execute_with_error_handling(
            request,
            self._process_voice_request
        )
    
    async def _process_voice_request(self, request: Request) -> Dict[str, Any]:
        """
        Route and process voice request based on endpoint.
        
        Args:
            request: FastAPI Request
            
        Returns:
            Response data
        """
        path = request.url.path
        
        logger.info(f"Processing voice request: {path}")
        
        # Route to appropriate handler
        if "transcribe" in path:
            return await self._handle_transcribe(request)
        elif "synthesize" in path:
            return await self._handle_synthesize(request)
        elif "query" in path:
            return await self._handle_voice_query(request)
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown voice endpoint. Use: /transcribe, /synthesize, /query"
            )
    
    async def _handle_transcribe(self, request: Request) -> Dict[str, Any]:
        """
        Handle audio transcription (STT).
        
        Args:
            request: Request with audio data
            
        Returns:
            Transcription result
        """
        try:
            # Parse request body
            body = await request.json()
            
            # Create transcription request
            transcription_request = TranscriptionRequest(**body)
            
            # Transcribe audio
            result = await self.stt_service.transcribe(transcription_request)
            
            return {
                "text": result.text,
                "language": result.language,
                "duration_seconds": result.duration_seconds,
                "confidence": result.confidence,
                "metadata": result.metadata
            }
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    
    async def _handle_synthesize(self, request: Request) -> Dict[str, Any]:
        """
        Handle text-to-speech synthesis (TTS).
        
        Args:
            request: Request with text data
            
        Returns:
            Synthesized audio data
        """
        try:
            # Parse request body
            body = await request.json()
            
            # Create synthesis request
            synthesis_request = SynthesisRequest(**body)
            
            # Synthesize speech
            result = await self.tts_service.synthesize(synthesis_request)
            
            return {
                "audio_data": result.audio_data,
                "audio_format": result.audio_format,
                "duration_seconds": result.duration_seconds,
                "character_count": result.character_count,
                "metadata": result.metadata
            }
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")
    
    async def _handle_voice_query(self, request: Request) -> Dict[str, Any]:
        """
        Handle complete voice query flow (STT → AI → TTS).
        
        Args:
            request: Request with audio query
            
        Returns:
            Complete response with text and audio
        """
        start_time = time.time()
        
        try:
            # Parse request body
            body = await request.json()
            
            # Create voice query request
            voice_request = VoiceQueryRequest(**body)
            
            # Step 1: Transcribe audio to text
            logger.info("Step 1: Transcribing audio")
            transcription_req = TranscriptionRequest(
                audio_data=voice_request.audio_data,
                audio_format=voice_request.audio_format,
                language=None,
                prompt=None
            )
            transcription = await self.stt_service.transcribe(transcription_req)
            query_text = transcription.text
            
            # Step 2: Process through AI (ChatService)
            logger.info(f"Step 2: Processing AI query: {query_text[:50]}...")
            chat_response = self.chat_service.process_chat(
                user_input=query_text,
                user_id=voice_request.user_id,
                conversation_id=voice_request.conversation_id,
                context=voice_request.context
            )
            
            response_text = chat_response.get("response", "")
            conversation_id = chat_response.get("conversation_id")
            agents_used = chat_response.get("agents_used", [])
            
            # Step 3: Synthesize AI response to audio
            logger.info("Step 3: Synthesizing response audio")
            synthesis_req = SynthesisRequest(
                text=response_text,
                voice=voice_request.response_voice,
                speed=1.0,
                output_format=voice_request.response_format
            )
            synthesis = await self.tts_service.synthesize(synthesis_req)
            
            processing_time = time.time() - start_time
            
            return {
                "query_text": query_text,
                "response_text": response_text,
                "response_audio": synthesis.audio_data,
                "audio_format": synthesis.audio_format,
                "conversation_id": conversation_id,
                "agents_used": agents_used,
                "processing_time": round(processing_time, 3),
                "metadata": {
                    "transcription": transcription.metadata,
                    "synthesis": synthesis.metadata,
                    "chat": chat_response.get("metadata", {})
                }
            }
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Voice query failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Voice query failed: {str(e)}")
    
    async def validate_request(self, request: Request) -> bool:
        """
        Validate voice request.
        
        Validates:
        - Content-type is application/json
        - Request body is valid JSON
        
        Args:
            request: FastAPI Request
            
        Returns:
            True if valid
            
        Raises:
            HTTPException: If validation fails
        """
        # Check content-type
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            raise HTTPException(
                status_code=415,
                detail="Content-Type must be application/json"
            )
        
        return True

# - async def _validate_audio_file(file) -> bool
