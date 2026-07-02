"""
ValuerOS — OCR Tasks
Document OCR processing via pdfplumber + pytesseract.
"""
from __future__ import annotations

import io
import json
import logging
from PIL import Image
import pdfplumber
import pytesseract
from openai import OpenAI

from app.celery_app import celery_app
from app.core.config import get_settings
from app.core.database import get_sync_db
from app.core.storage import get_minio_client
from app.models.models import Document

logger = logging.getLogger(__name__)
settings = get_settings()


def extract_text_from_bytes(file_bytes: bytes, mime_type: str | None) -> str:
    text = ""
    try:
        if mime_type == "application/pdf":
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        elif mime_type in ["image/png", "image/jpeg", "image/jpg"]:
            image = Image.open(io.BytesIO(file_bytes))
            text = pytesseract.image_to_string(image)
    except Exception as e:
        logger.error(f"Error during text extraction: {str(e)}")
    return text


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_ocr(self, document_id: str) -> dict:
    """
    Extract text from an uploaded document using OCR.
    Updates Document.ocr_raw_text and ocr_status on completion.
    """
    db = get_sync_db()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return {"status": "error", "message": "Document not found"}

        document.ocr_status = "processing"
        db.commit()

        # Download from MinIO
        minio_client = get_minio_client()
        try:
            response = minio_client.get_object(settings.minio_bucket, document.minio_path)
            file_bytes = response.read()
        finally:
            response.close()
            response.release_conn()

        # Extract text
        text = extract_text_from_bytes(file_bytes, document.mime_type)

        document.ocr_raw_text = text
        document.ocr_status = "completed"
        document.ocr_confidence = 0.95 if text else 0.0
        db.commit()

        return {"document_id": document_id, "status": "completed", "text_length": len(text)}
    except Exception as exc:
        db.rollback()
        logger.error(f"Error in process_ocr: {str(exc)}")
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def extract_structured_data(self, document_id: str) -> dict:
    """
    Use LLM to extract structured fields from OCR'd text.
    Updates Document.extracted_data on completion.
    """
    db = get_sync_db()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return {"status": "error", "message": "Document not found"}

        if not document.ocr_raw_text:
            return {"status": "error", "message": "No OCR text available for extraction"}

        # If no API key is set, use a mock extraction for testing/MVP
        if not settings.openai_api_key:
            mock_data = {
                "property_type": "residential",
                "year_built": 2015,
                "bedrooms": 3,
                "bathrooms": 2.5,
                "gross_building_area_sqft": 2100,
                "lot_size_sqft": 7500,
                "address": "123 Main St, Springfield",
            }
            document.extracted_data = mock_data
            db.commit()
            return {"document_id": document_id, "status": "completed", "extracted_data": mock_data}

        # Call OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        prompt = f"""
        You are an expert real estate data extraction assistant.
        Extract the following fields from the provided real estate document text:
        - property_type (residential, commercial, land, industrial)
        - year_built (integer)
        - bedrooms (integer)
        - bathrooms (float)
        - gross_building_area_sqft (float)
        - lot_size_sqft (float)
        - address (string)

        Return the result ONLY as a valid JSON object. Do not include any markdown formatting or explanations.

        Document Text:
        {document.ocr_raw_text[:4000]}
        """

        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )

        content = response.choices[0].message.content
        if content:
            # Clean up potential markdown code blocks
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            extracted_data = json.loads(content.strip())
        else:
            extracted_data = {}

        document.extracted_data = extracted_data
        db.commit()

        return {"document_id": document_id, "status": "completed", "extracted_data": extracted_data}
    except Exception as exc:
        db.rollback()
        logger.error(f"Error in extract_structured_data: {str(exc)}")
        raise self.retry(exc=exc)
    finally:
        db.close()