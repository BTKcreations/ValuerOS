"""
ValuerOS — Pydantic Schemas: Document
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    mime_type: Optional[str]
    file_size_bytes: Optional[int]
    doc_type: Optional[str]
    ocr_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: str
    property_id: Optional[str]
    valuation_id: Optional[str]
    filename: str
    mime_type: Optional[str]
    file_size_bytes: Optional[int]
    doc_type: Optional[str]
    ocr_status: str
    ocr_confidence: Optional[float]
    extracted_data: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentExtractedResponse(BaseModel):
    id: str
    ocr_status: str
    ocr_raw_text: Optional[str]
    ocr_confidence: Optional[float]
    extracted_data: dict[str, Any]