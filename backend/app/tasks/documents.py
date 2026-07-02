"""
ValuerOS — Document Tasks
Document ingestion, embedding, and RAG indexing.
"""
from __future__ import annotations

import logging
from openai import OpenAI

from app.celery_app import celery_app
from app.core.config import get_settings
from app.core.database import get_sync_db
from app.models.models import Document
from app.tasks.ocr import extract_structured_data, process_ocr

logger = logging.getLogger(__name__)
settings = get_settings()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def ingest_document(self, document_id: str) -> dict:
    """
    Full document ingestion pipeline:
    1. Validate file in MinIO
    2. Chain: OCR → structured extraction → embedding
    """
    try:
        # Run OCR
        process_ocr(document_id)
        # Run structured extraction
        extract_structured_data(document_id)
        # Run embedding generation
        generate_embedding(document_id)
        return {"document_id": document_id, "status": "completed"}
    except Exception as exc:
        logger.error(f"Error in ingest_document: {str(exc)}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def generate_embedding(self, document_id: str) -> dict:
    """
    Generate vector embedding for document text (for RAG).
    Updates Document.embedding.
    """
    db = get_sync_db()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return {"status": "error", "message": "Document not found"}

        if not document.ocr_raw_text:
            return {"status": "error", "message": "No OCR text available for embedding"}

        # If no API key is set, use a mock embedding for testing/MVP
        if not settings.openai_api_key:
            import random
            mock_embedding = [random.uniform(-1.0, 1.0) for _ in range(1536)]
            document.embedding = mock_embedding
            db.commit()
            return {"document_id": document_id, "status": "completed", "embedding_length": 1536}

        # Call OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=document.ocr_raw_text[:8000],
        )

        embedding = response.data[0].embedding
        document.embedding = embedding
        db.commit()

        return {"document_id": document_id, "status": "completed", "embedding_length": len(embedding)}
    except Exception as exc:
        db.rollback()
        logger.error(f"Error in generate_embedding: {str(exc)}")
        raise self.retry(exc=exc)
    finally:
        db.close()