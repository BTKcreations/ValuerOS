"""
ValuerOS — SQLAlchemy ORM Models
Core domain models: User, Property, Valuation, ComparableSale, Document, Report.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from geoalchemy2 import Geometry
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def _new_uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ----------------------------------------------------------------
# User
# ----------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_new_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="appraiser")
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    valuations = relationship("Valuation", back_populates="appraiser")


# ----------------------------------------------------------------
# Property
# ----------------------------------------------------------------
class Property(Base):
    __tablename__ = "properties"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_new_uuid)
    parcel_number = Column(String(100), unique=True, index=True)
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255))
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(50), nullable=False, index=True)
    zip_code = Column(String(20), nullable=False, index=True)
    location = Column(Geometry("POINT", srid=4326))
    property_type = Column(String(50), nullable=False, index=True)
    sub_type = Column(String(50))
    year_built = Column(Integer)
    lot_size_sqft = Column(Float)
    gross_building_area_sqft = Column(Float)
    bedrooms = Column(Integer)
    bathrooms = Column(Float)
    property_metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    valuations = relationship("Valuation", back_populates="property")
    documents = relationship("Document", back_populates="property")

    @property
    def latitude(self) -> float | None:
        if self.location is not None:
            from geoalchemy2.shape import to_shape
            try:
                return to_shape(self.location).y
            except Exception:
                pass
        return None

    @property
    def longitude(self) -> float | None:
        if self.location is not None:
            from geoalchemy2.shape import to_shape
            try:
                return to_shape(self.location).x
            except Exception:
                pass
        return None


# ----------------------------------------------------------------
# Valuation
# ----------------------------------------------------------------
class Valuation(Base):
    __tablename__ = "valuations"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_new_uuid)
    property_id = Column(UUID(as_uuid=False), ForeignKey("properties.id"), nullable=False, index=True)
    appraiser_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="draft", index=True)
    valuation_date = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    effective_date = Column(DateTime(timezone=True))
    purpose = Column(String(100), default="market_value")
    approach = Column(String(50), default="sales_comparison")
    final_value = Column(Float)
    value_range_low = Column(Float)
    value_range_high = Column(Float)
    confidence_score = Column(Float)
    methodology_notes = Column(Text)
    adjustments = Column(JSONB, default=dict)
    ml_model_version = Column(String(50))
    ml_prediction = Column(Float)
    ml_features = Column(JSONB, default=dict)
    workflow_state = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    property = relationship("Property", back_populates="valuations")
    appraiser = relationship("User", back_populates="valuations")
    comparable_sales = relationship("ComparableSale", back_populates="valuation")
    report = relationship("Report", back_populates="valuation", uselist=False)


# ----------------------------------------------------------------
# ComparableSale
# ----------------------------------------------------------------
class ComparableSale(Base):
    __tablename__ = "comparable_sales"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_new_uuid)
    valuation_id = Column(UUID(as_uuid=False), ForeignKey("valuations.id"), nullable=False, index=True)
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(50), nullable=False)
    zip_code = Column(String(20))
    location = Column(Geometry("POINT", srid=4326))
    sale_date = Column(DateTime(timezone=True))
    sale_price = Column(Float)
    property_type = Column(String(50))
    gross_building_area_sqft = Column(Float)
    lot_size_sqft = Column(Float)
    year_built = Column(Integer)
    bedrooms = Column(Integer)
    bathrooms = Column(Float)
    distance_miles = Column(Float)
    adjustment_factor = Column(Float, default=1.0)
    adjusted_price = Column(Float)
    weight = Column(Float, default=1.0)
    source = Column(String(100))
    comp_metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    valuation = relationship("Valuation", back_populates="comparable_sales")


# ----------------------------------------------------------------
# Document
# ----------------------------------------------------------------
class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_new_uuid)
    property_id = Column(UUID(as_uuid=False), ForeignKey("properties.id"), index=True)
    valuation_id = Column(UUID(as_uuid=False), ForeignKey("valuations.id"), index=True)
    filename = Column(String(500), nullable=False)
    minio_path = Column(String(500), nullable=False)
    mime_type = Column(String(100))
    file_size_bytes = Column(Integer)
    doc_type = Column(String(50), index=True)
    ocr_status = Column(String(50), default="pending", index=True)
    ocr_raw_text = Column(Text)
    ocr_confidence = Column(Float)
    extracted_data = Column(JSONB, default=dict)
    embedding = Column(Vector(1536))
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    property = relationship("Property", back_populates="documents")


# ----------------------------------------------------------------
# Report
# ----------------------------------------------------------------
class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_new_uuid)
    valuation_id = Column(UUID(as_uuid=False), ForeignKey("valuations.id"), nullable=False, unique=True, index=True)
    status = Column(String(50), default="draft", index=True)
    minio_path = Column(String(500))
    narrative = Column(Text)
    template_version = Column(String(50))
    report_metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    valuation = relationship("Valuation", back_populates="report")