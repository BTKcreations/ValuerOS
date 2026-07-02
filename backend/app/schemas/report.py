"""
ValuerOS — Pydantic Schemas: Report
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class ReportGenerateRequest(BaseModel):
    template_version: Optional[str] = "1.0"
    include_narrative: bool = True
    include_comps_grid: bool = True
    include_photos: bool = True
    include_charts: bool = True


class ReportResponse(BaseModel):
    id: str
    valuation_id: str
    status: str
    narrative: Optional[str]
    template_version: Optional[str]
    report_metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportDownloadResponse(BaseModel):
    download_url: str
    filename: str
    expires_in_seconds: int = 3600