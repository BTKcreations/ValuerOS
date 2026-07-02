"""
ValuerOS — Properties API routes.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from geoalchemy2.functions import ST_MakePoint, ST_SetSRID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import Property
from app.schemas.property import PropertyCreate, PropertyListResponse, PropertyResponse, PropertyUpdate

router = APIRouter()


@router.post("/", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_property(
    property_in: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # noqa: B008
):
    """Create a new property record."""
    # Check for existing property by parcel number if provided
    if property_in.parcel_number:
        stmt = select(Property).where(Property.parcel_number == property_in.parcel_number)
        result = await db.execute(stmt)
        existing_property = result.scalar_one_or_none()
        if existing_property:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Property with this parcel number already exists.",
            )

    property_data = property_in.model_dump(exclude_unset=True)

    # Handle geospatial data
    latitude = property_data.pop("latitude", None)
    longitude = property_data.pop("longitude", None)
    if latitude is not None and longitude is not None:
        # Create a PostGIS POINT geometry with SRID 4326 (WGS 84)
        property_data["location"] = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)

    db_property = Property(**property_data)
    db.add(db_property)
    await db.commit()
    await db.refresh(db_property)
    return db_property


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # noqa: B008
):
    """Get a single property by ID."""
    stmt = select(Property).where(Property.id == property_id)
    result = await db.execute(stmt)
    property = result.scalar_one_or_none()
    if not property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    return property


@router.get("/", response_model=PropertyListResponse)
async def list_properties(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # noqa: B008
):
    """List all properties with optional search/filter."""
    stmt = select(Property).offset(skip).limit(limit)
    result = await db.execute(stmt)
    properties = result.scalars().all()

    count_stmt = select(func.count()).select_from(Property)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    return {
        "items": properties,
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit,
    }


@router.get("/{property_id}/comps")
async def find_comparables(
    property_id: str,
    radius_miles: float = 5.0,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # noqa: B008
):
    """Find comparable sales near a property (geospatial radius search)."""
    # 1. Get the target property
    stmt = select(Property).where(Property.id == property_id)
    result = await db.execute(stmt)
    target_property = result.scalar_one_or_none()
    if not target_property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    if not target_property.location:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Property has no location data for geospatial search.",
        )

    # 2. Find comparables within radius (using PostGIS ST_DWithin)
    # 1 mile is approx 1609.34 meters. Since SRID 4326 uses degrees, we cast to geography for meters.
    from sqlalchemy import cast
    from geoalchemy2 import Geography
    from app.models.models import ComparableSale

    radius_meters = radius_miles * 1609.34
    
    comps_stmt = select(ComparableSale).where(
        func.ST_DWithin(
            cast(ComparableSale.location, Geography),
            cast(target_property.location, Geography),
            radius_meters
        )
    ).limit(10)
    
    comps_result = await db.execute(comps_stmt)
    comps = comps_result.scalars().all()

    return {"property_id": property_id, "comps": comps}