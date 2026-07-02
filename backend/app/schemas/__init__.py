"""
ValuerOS — Pydantic Schemas package.
Re-exports all domain schemas.
"""
from app.schemas.user import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from app.schemas.property import (
    PropertyCreate,
    PropertyListResponse,
    PropertyResponse,
    PropertyUpdate,
)
from app.schemas.valuation import (
    ComparableSaleResponse,
    ValuationCreate,
    ValuationProgressResponse,
    ValuationResponse,
    ValuationUpdate,
)
from app.schemas.document import (
    DocumentExtractedResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from app.schemas.report import (
    ReportDownloadResponse,
    ReportGenerateRequest,
    ReportResponse,
)

__all__ = [
    # User
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserUpdate",
    "TokenResponse",
    # Property
    "PropertyCreate",
    "PropertyUpdate",
    "PropertyResponse",
    "PropertyListResponse",
    # Valuation
    "ValuationCreate",
    "ValuationUpdate",
    "ValuationResponse",
    "ValuationProgressResponse",
    "ComparableSaleResponse",
    # Document
    "DocumentUploadResponse",
    "DocumentResponse",
    "DocumentExtractedResponse",
    # Report
    "ReportGenerateRequest",
    "ReportResponse",
    "ReportDownloadResponse",
]