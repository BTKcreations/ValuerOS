"""
ValuerOS — Pydantic Schemas: Property
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class PropertyCreate(BaseModel):
    parcel_number: Optional[str] = Field(default=None, max_length=100)
    address_line1: str = Field(..., min_length=1, max_length=255)
    address_line2: Optional[str] = Field(default=None, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=50)
    zip_code: str = Field(..., min_length=5, max_length=20)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    property_type: str = Field(..., pattern=r"^(residential|commercial|land|industrial)$")
    sub_type: Optional[str] = Field(default=None, max_length=50)
    year_built: Optional[int] = Field(default=None, ge=1700, le=2100)
    lot_size_sqft: Optional[float] = Field(default=None, gt=0)
    gross_building_area_sqft: Optional[float] = Field(default=None, gt=0)
    bedrooms: Optional[int] = Field(default=None, ge=0)
    bathrooms: Optional[float] = Field(default=None, ge=0)
    property_metadata: dict[str, Any] = Field(default_factory=dict)


class PropertyUpdate(BaseModel):
    address_line1: Optional[str] = Field(default=None, min_length=1, max_length=255)
    address_line2: Optional[str] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, min_length=1, max_length=100)
    state: Optional[str] = Field(default=None, min_length=2, max_length=50)
    zip_code: Optional[str] = Field(default=None, min_length=5, max_length=20)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    property_type: Optional[str] = Field(default=None, pattern=r"^(residential|commercial|land|industrial)$")
    sub_type: Optional[str] = Field(default=None, max_length=50)
    year_built: Optional[int] = Field(default=None, ge=1700, le=2100)
    lot_size_sqft: Optional[float] = Field(default=None, gt=0)
    gross_building_area_sqft: Optional[float] = Field(default=None, gt=0)
    bedrooms: Optional[int] = Field(default=None, ge=0)
    bathrooms: Optional[float] = Field(default=None, ge=0)
    property_metadata: Optional[dict[str, Any]] = None


class PropertyResponse(BaseModel):
    id: str
    parcel_number: Optional[str]
    address_line1: str
    address_line2: Optional[str]
    city: str
    state: str
    zip_code: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    property_type: str
    sub_type: Optional[str]
    year_built: Optional[int]
    lot_size_sqft: Optional[float]
    gross_building_area_sqft: Optional[float]
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    property_metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PropertyListResponse(BaseModel):
    items: list[PropertyResponse]
    total: int
    page: int
    page_size: int