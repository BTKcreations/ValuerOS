"""
ValuerOS — Celery Application
Async task queue for document processing, OCR, ML inference, and report generation.
"""
from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "valueros",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.ocr",
        "app.tasks.ml",
        "app.tasks.reports",
        "app.tasks.documents",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue="valueros",
    task_routes={
        "app.tasks.ocr.*": {"queue": "ocr"},
        "app.tasks.ml.*": {"queue": "ml"},
        "app.tasks.reports.*": {"queue": "reports"},
        "app.tasks.documents.*": {"queue": "documents"},
    },
)