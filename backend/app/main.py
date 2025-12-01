"""
AI Meeting Assistant - Main Application Entry

This is the main entry point for the FastAPI application.
Run with: uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Handles startup and shutdown events:
    - Startup: Initialize database tables
    - Shutdown: Clean up resources (if needed)
    """
    # Startup: Initialize database
    await init_db()
    yield
    # Shutdown: Clean up resources (if needed)


# Create FastAPI application instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="An AI-powered meeting management system that helps automatically generate meeting minutes, extract action items, and integrate with external task systems.",
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint.

    Returns the service status, version, and current timestamp.
    Use this endpoint to verify the service is running correctly.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/", tags=["System"])
async def root():
    """
    Root endpoint.

    Returns a welcome message and links to documentation.
    """
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }
