"""
FastAPI application bootstrap.

Initializes the FastAPI application, configures middleware,
registers API routers, and sets up startup/shutdown events.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment variables (useful for local development)
load_dotenv()

# Configuration
APP_NAME = os.getenv("APP_NAME") or "HybridGraphRAG API"
APP_VERSION = os.getenv("APP_VERSION") or "1.0.0"
APP_ENV = os.getenv("APP_ENV") or "development"
ALLOWED_ORIGINS_ENV = os.getenv("ALLOWED_ORIGINS") or "*"
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS_ENV.split(",") if origin.strip()]

# Internal modules
from backend.app.api import document_router, user_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    Setup operations before accepting requests and cleanup after shutdown.
    """
    # Startup: Initialize connections (Database engine, MinIO, etc. are handled lazily or via dependencies,
    # but we could add explicit initializations here if needed)
    yield
    # Shutdown: Clean up connections


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        description="Enterprise Knowledge Assistant API",
        lifespan=lifespan,
    )

    # Configure CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Routers
    app.include_router(user_router)
    app.include_router(document_router)

    # Health Endpoint
    @app.get("/health", tags=["Health"])
    async def health_check() -> JSONResponse:
        """Health check endpoint to verify the service is running."""
        return JSONResponse(
            content={
                "status": "healthy",
                "service": APP_NAME,
                "environment": APP_ENV,
                "version": APP_VERSION,
            }
        )

    return app


# Create the global application instance
app = create_app()
