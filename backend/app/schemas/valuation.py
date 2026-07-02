"""
ValuerOS — Pydantic Schemas: Valuation
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ValuationCreate(BaseModel):
    property_id: str
    purpose: str = Field(default="market_value", pattern=r"^(market_value|refinance|insurance|tax_appeal)$")
    approach: str = Field(default="sales_comparison", pattern=r"^(sales_comparison|income|cost|hybrid)$")
    effective_date: Optional[datetime] = None
    methodology_notes: Optional[str] = None


class ValuationUpdate(BaseModel):
    status: Optional[str] = None
    purpose: Optional[str] = Field(default=None, pattern=r"^(market_value|refinance|insurance|tax_appeal)$")
    approach: Optional[str] = Field(default=None, pattern=r"^(sales_comparison|income|cost|hybrid)$")
    effective_date: Optional[datetime] = None
    final_value: Optional[float] = None
    value_range_low: Optional[float] = None
    value_range_high: Optional[float] = None
    confidence_score: Optional[float] = Field(default=None, ge=0, le=1)
    methodology_notes: Optional[str] = None
    adjustments: Optional[dict[str, Any]] = None


class ValuationResponse(BaseModel):
    id: str
    property_id: str
    appraiser_id: str
    status: str
    valuation_date: datetime
    effective_date: Optional[datetime]
    purpose: str
    approach: str
    final_value: Optional[float]
    value_range_low: Optional[float]
    value_range_high: Optional[float]
    confidence_score: Optional[float]
    methodology_notes: Optional[str]
    adjustments: dict[str, Any]
    ml_model_version: Optional[str]
    ml_prediction: Optional[float]
    ml_features: dict[str, Any]
    workflow_state: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ValuationProgressResponse(BaseModel):
    valuation_id: str
    status: str
    workflow_state: dict[str, Any]
    steps: list[dict[str, Any]] = Field(default_factory=list)


class ComparableSaleResponse(BaseModel):
    id: str
    address: str
    city: str
    state: str
    zip_code: Optional[str]
    sale_date: Optional[datetime]
    sale_price: Optional[float]
    property_type: Optional[str]
    gross_building_area_sqft: Optional[float]
    lot_size_sqft: Optional[float]
    year_built: Optional[int]
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    distance_miles: Optional[float]
    adjustment_factor: float
    adjusted_price: Optional[float]
    weight: float
    source: Optional[str]

    model_config = {"from_attributes": True}