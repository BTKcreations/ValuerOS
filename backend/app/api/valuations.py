"""
ValuerOS — Valuations API routes.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import Property, Valuation
from app.schemas.valuation import ValuationCreate, ValuationProgressResponse, ValuationResponse

router = APIRouter()


@router.post("/", response_model=ValuationResponse, status_code=status.HTTP_201_CREATED)
async def create_valuation(
    valuation_in: ValuationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # noqa: B008
):
    """Start a new valuation workflow for a property."""
    # Verify property exists
    stmt = select(Property).where(Property.id == valuation_in.property_id)
    result = await db.execute(stmt)
    property = result.scalar_one_or_none()
    if not property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    # Create valuation
    db_valuation = Valuation(
        property_id=valuation_in.property_id,
        appraiser_id=current_user["id"],
        purpose=valuation_in.purpose,
        approach=valuation_in.approach,
        effective_date=valuation_in.effective_date,
        methodology_notes=valuation_in.methodology_notes,
        status="draft",
        workflow_state={"current_step": "created", "steps_completed": []},
    )
    db.add(db_valuation)
    await db.commit()
    await db.refresh(db_valuation)
    return db_valuation


@router.get("/{valuation_id}", response_model=ValuationResponse)
async def get_valuation(
    valuation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # noqa: B008
):
    """Get valuation status and results."""
    stmt = select(Valuation).where(Valuation.id == valuation_id)
    result = await db.execute(stmt)
    valuation = result.scalar_one_or_none()
    if not valuation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Valuation not found")
    return valuation


@router.get("/{valuation_id}/progress", response_model=ValuationProgressResponse)
async def get_valuation_progress(
    valuation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # noqa: B008
):
    """Get step-by-step workflow progress."""
    stmt = select(Valuation).where(Valuation.id == valuation_id)
    result = await db.execute(stmt)
    valuation = result.scalar_one_or_none()
    if not valuation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Valuation not found")
    
    return {
        "valuation_id": valuation.id,
        "status": valuation.status,
        "workflow_state": valuation.workflow_state or {},
        "steps": valuation.workflow_state.get("steps_completed", []) if valuation.workflow_state else [],
    }