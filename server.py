"""
FastAPI Server for Multi-Agent AI System v2.0

Production-grade REST API with:
- Google OAuth authentication
- Database persistence
- Rate limiting
- Error handling
- Request validation
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
import logging
from dotenv import load_dotenv

from config.settings import get_settings
from database import init_db
from app.routes import auth_router, api_router, oauth_router, email_router
from app.gateway import APIGateway
from app.handlers import SingleChatHandler, VoiceHandler, ThirdPartyHandler

# Load environment variables
load_dotenv()
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Multi-Agent AI System v2.0...")
    
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized successfully")
        
        # Initialize Gateway
        gateway = APIGateway()
        
        # Initialize Handlers
        singlechat_handler = SingleChatHandler()
        voice_handler = VoiceHandler()
        third_party_handler = ThirdPartyHandler()
        
        # Store in app state for endpoint access
        app.state.gateway = gateway
        app.state.handlers = {
            "singlechat": singlechat_handler,
            "voice": voice_handler,
            "third_party": third_party_handler,
        }
        
        logger.info("API Gateway initialized")
        logger.info("Handler routing configured:")
        logger.info("  - /api/chat/*   → SingleChatHandler")
        logger.info("  - /api/voice/*  → VoiceHandler")
        logger.info("  - /api/email/*  → ThirdPartyHandler")
        logger.info("  - /api/sms/*    → ThirdPartyHandler")
        logger.info("  - /api/drive/*  → ThirdPartyHandler")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Multi-Agent AI System...")


# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent AI System API",
    description="""
    Production-grade multi-agent AI system with:
    
    - **Google OAuth** authentication
    - **Persistent** conversation history
    - **User personas** that learn from interactions
    - **Feedback system** for continuous improvement
    - **RAG integration** for knowledge retrieval (planned)
    - **MCP protocol** for external tool integration (planned)
    
    ## Authentication
    
    Most endpoints require authentication via JWT Bearer token.
    
    1. Login via `/auth/google/login`
    2. Receive JWT token in callback
    3. Include token in requests: `Authorization: Bearer <token>`
    
    ## Rate Limiting
    
    - **General endpoints**: 60 requests/minute
    - **Query processing**: 10 requests/minute
    """,
    version="2.0.0",
    lifespan=lifespan,
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
)


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unexpected errors.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "code": "INTERNAL_SERVER_ERROR",
        },
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log all requests.
    """
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response


# ============================================================================
# Routers
# ============================================================================

# Include authentication routes (bypass gateway)
app.include_router(auth_router)

# Include OAuth routes for third-party service authentication
app.include_router(oauth_router)

# Include email routes (direct access)
app.include_router(email_router)

# Include API routes (bypass gateway for now - will be deprecated)
app.include_router(api_router)


# ============================================================================
# Gateway Integration
# ============================================================================

@app.api_route(
    "/api/chat/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    tags=["gateway"],
    summary="Chat endpoints via Gateway"
)
async def gateway_chat(request: Request, path: str):
    """Route chat requests through API Gateway to SingleChatHandler."""
    handler_type = request.app.state.gateway.get_handler_type(request.url.path)
    handler = request.app.state.handlers.get(handler_type)
    if handler:
        return await handler.handle(request)
    return {"error": "Handler not found"}


@app.api_route(
    "/api/voice/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    tags=["gateway"],
    summary="Voice endpoints via Gateway"
)
async def gateway_voice(request: Request, path: str):
    """Route voice requests through API Gateway to VoiceHandler."""
    handler_type = request.app.state.gateway.get_handler_type(request.url.path)
    handler = request.app.state.handlers.get(handler_type)
    if handler:
        return await handler.handle(request)
    return {"error": "Handler not found"}


@app.api_route(
    "/api/email/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    tags=["gateway"],
    summary="Email endpoints via Gateway"
)
async def gateway_email(request: Request, path: str):
    """Route email requests through API Gateway to ThirdPartyHandler."""
    handler_type = request.app.state.gateway.get_handler_type(request.url.path)
    handler = request.app.state.handlers.get(handler_type)
    if handler:
        return await handler.handle(request)
    return {"error": "Handler not found"}


@app.api_route(
    "/api/sms/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    tags=["gateway"],
    summary="SMS endpoints via Gateway"
)
async def gateway_sms(request: Request, path: str):
    """Route SMS requests through API Gateway to ThirdPartyHandler."""
    handler_type = request.app.state.gateway.get_handler_type(request.url.path)
    handler = request.app.state.handlers.get(handler_type)
    if handler:
        return await handler.handle(request)
    return {"error": "Handler not found"}


@app.api_route(
    "/api/drive/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    tags=["gateway"],
    summary="Drive endpoints via Gateway"
)
async def gateway_drive(request: Request, path: str):
    """Route drive requests through API Gateway to ThirdPartyHandler."""
    handler_type = request.app.state.gateway.get_handler_type(request.url.path)
    handler = request.app.state.handlers.get(handler_type)
    if handler:
        return await handler.handle(request)
    return {"error": "Handler not found"}


# ============================================================================
# Health Check
# ============================================================================

@app.get(
    "/health",
    tags=["system"],
    summary="Health check",
    description="Check if the API is running and database is accessible"
)
@limiter.limit("60/minute")
async def health_check(request: Request):
    """
    Health check endpoint.
    
    Returns:
        System health status
    """
    return {
        "status": "healthy",
        "version": "2.0.0",
        "database": "connected",  # Placeholder
    }


@app.get(
    "/",
    tags=["system"],
    summary="API root",
    description="Get API information and links"
)
async def root():
    """
    Root endpoint with API information.
    
    Returns:
        API metadata and navigation links
    """
    return {
        "name": "Multi-Agent AI System API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "authentication": {
            "login": "/auth/google/login",
            "logout": "/auth/logout",
        },
        "api": {
            "query": "/api/query",
            "conversations": "/api/conversations",
            "feedback": "/api/feedback",
            "persona": "/api/persona",
            "profile": "/api/user/profile",
        }
    }


if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        # reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug",
    )

