"""
ValuerOS — API Router aggregator.
All domain routers are mounted here.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api import auth, documents, properties, reports, valuations

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(properties.router, prefix="/properties", tags=["Properties"])
api_router.include_router(valuations.router, prefix="/valuations", tags=["Valuations"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])