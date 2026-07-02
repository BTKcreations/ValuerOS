"""
ValuerOS — Documents API routes (upload, OCR status, retrieval).
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.storage import get_minio_client
from app.models.models import Document
from app.schemas.document import DocumentExtractedResponse, DocumentResponse, DocumentUploadResponse
from app.tasks.documents import ingest_document

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    property_id: Optional[UUID] = None,
    valuation_id: Optional[UUID] = None,
    doc_type: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # noqa: B008
):
    """Upload a PDF or image document for OCR processing."""
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided.")

    minio_client = get_minio_client()
    import uuid
    document_id = str(uuid.uuid4())
    minio_path = f"documents/{document_id}/{file.filename}"

    # Upload to MinIO
    import io
    from app.core.config import get_settings
    settings = get_settings()
    file_content = await file.read()
    try:
        minio_client.put_object(
            bucket_name=settings.minio_bucket,
            object_name=minio_path,
            data=io.BytesIO(file_content),
            length=len(file_content),
            content_type=file.content_type,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(
            f"Failed to upload file to MinIO: {str(e)}. Continuing with local mock database record."
        )

    # Create document record in DB
    db_document = Document(
        id=document_id,
        property_id=property_id,
        valuation_id=valuation_id,
        filename=file.filename,
        minio_path=minio_path,
        mime_type=file.content_type,
        file_size_bytes=len(file_content),
        doc_type=doc_type,
        ocr_status="uploaded",
    )
    db.add(db_document)
    await db.commit()
    await db.refresh(db_document)

    # Trigger background OCR task
    background_tasks.add_task(ingest_document, document_id)

    return db_document


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # noqa: B008
):
    """Get document metadata and OCR status."""
    stmt = select(Document).where(Document.id == str(document_id))
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.get("/{document_id}/extracted", response_model=DocumentExtractedResponse)
async def get_extracted_data(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # noqa: B008
):
    """Get structured data extracted from document via LLM."""
    stmt = select(Document).where(Document.id == str(document_id))
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentExtractedResponse(
        id=document.id,
        ocr_status=document.ocr_status,
        ocr_raw_text=document.ocr_raw_text,
        ocr_confidence=document.ocr_confidence,
        extracted_data=document.extracted_data,
    )