"""
ValuerOS — FastAPI Application Entry Point
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    # Startup: nothing needed yet (DB, MinIO, Redis are external services)
    yield
    # Shutdown: clean up connections
    from app.core.database import engine
    await engine.dispose()


app = FastAPI(
    title="ValuerOS API",
    description="AI-Powered Real Estate Property Valuation Automation System",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routers under /api
app.include_router(api_router, prefix="/api")


@app.get("/api/health", tags=["System"])
async def health_check():
    """Health check endpoint for Docker / monitoring."""
    return {"status": "ok", "version": "0.1.0", "environment": settings.app_env}