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
from backend.app.api import (
    document_router, user_router, chat_router, 
    audio_router, auth_router, workspace_router, conversation_router
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    Setup operations before accepting requests and cleanup after shutdown.
    """
    import logging
    logger = logging.getLogger("backend.startup")
    
    # 1. PostgreSQL Check
    from backend.app.database.session import engine
    from sqlalchemy import text
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✓ PostgreSQL connected")
    except Exception as e:
        logger.error(f"✗ PostgreSQL connection failed: {e}")
        raise

    # 2. Neo4j Check & Initialization
    from backend.app.storage.neo4j_service import Neo4jService
    try:
        neo4j = Neo4jService()
        neo4j._driver.verify_connectivity()
        neo4j.initialize_constraints()
        logger.info("✓ Neo4j connected")
    except Exception as e:
        logger.error(f"✗ Neo4j connection failed: {e}")
        raise
    finally:
        neo4j.close()

    # 3. Qdrant Check
    from backend.app.storage.qdrant_service import QdrantService
    try:
        qdrant = QdrantService()
        qdrant._client.get_collections()
        logger.info("✓ Qdrant connected")
    except Exception as e:
        logger.error(f"✗ Qdrant connection failed: {e}")
        raise

    # 4. MinIO Check
    from backend.app.storage.storage_service import StorageService
    try:
        minio = StorageService()
        minio._client.list_buckets()
        logger.info("✓ MinIO connected")
    except Exception as e:
        logger.error(f"✗ MinIO connection failed: {e}")
        raise

    logger.info("ASKME backend ready")
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

    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(workspace_router)
    app.include_router(conversation_router)
    app.include_router(document_router)
    app.include_router(chat_router)
    app.include_router(audio_router)

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
