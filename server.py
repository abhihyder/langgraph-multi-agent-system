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
from app.routes import auth_router, api_router

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
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
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

# Include authentication routes
app.include_router(auth_router)

# Include API routes
app.include_router(api_router)


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
    # Check if API key is configured (using settings from module level)
    api_key_configured = bool(settings.OPENAI_API_KEY)
    
    return {
        "status": "healthy",
        "version": "2.0.0",
        "database": "connected",  # Placeholder
        "api_key_configured": api_key_configured,
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

