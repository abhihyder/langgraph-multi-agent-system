"""
CORS Middleware Configuration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure this based on your needs
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
