"""
FastAPI Server for Agentic AI System

Provides REST API endpoints for the multi-agent system.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os
from dotenv import load_dotenv

from app import run_agent_system

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Agentic AI System API",
    description="Multi-agent AI system with Boss-Agent architecture",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    verbose: bool = False


class ChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    selected_agents: Optional[list[str]] = None


class HealthResponse(BaseModel):
    status: str
    api_key_configured: bool


# API Endpoints
@app.get("/", response_model=dict)
async def root():
    """Root endpoint - API info"""
    return {
        "message": "Agentic AI System API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "chat": "/api/chat",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    api_key_configured = bool(os.getenv("OPENAI_API_KEY"))
    return {
        "status": "healthy",
        "api_key_configured": api_key_configured
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint - processes user messages through the agent system
    
    Args:
        request: ChatRequest with user message
        
    Returns:
        ChatResponse with agent's response
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=500, 
            detail="OpenAI API key not configured"
        )
    
    try:
        # Run the agent system
        response = run_agent_system(request.message, verbose=request.verbose)
        
        return ChatResponse(
            response=response,
            intent=None,  # Can be extracted from state if needed
            selected_agents=None  # Can be extracted from state if needed
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@app.get("/api/agents", response_model=dict)
async def get_agents():
    """Get list of available agents"""
    return {
        "agents": [
            {
                "name": "research",
                "description": "Provides factual information and analysis"
            },
            {
                "name": "writing",
                "description": "Creates well-structured content"
            },
            {
                "name": "code",
                "description": "Generates production-quality code"
            }
        ]
    }


if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
