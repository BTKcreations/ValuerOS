"""
ValuerOS — Reports API routes (generate, download PDF).
"""
from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.storage import get_minio_client
from app.models.models import Report, Valuation
from app.schemas.report import ReportDownloadResponse, ReportGenerateRequest, ReportResponse
from app.tasks.reports import generate_report as generate_report_task

router = APIRouter()


@router.post("/{valuation_id}/generate", response_model=ReportResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_report(
    valuation_id: UUID,
    request: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # noqa: B008
):
    """Generate a valuation report PDF from completed valuation."""
    # Verify valuation exists
    stmt = select(Valuation).where(Valuation.id == str(valuation_id))
    result = await db.execute(stmt)
    valuation = result.scalar_one_or_none()
    if not valuation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Valuation not found")

    # Check if report already exists
    stmt_report = select(Report).where(Report.valuation_id == str(valuation_id))
    result_report = await db.execute(stmt_report)
    report = result_report.scalar_one_or_none()

    if not report:
        report = Report(
            valuation_id=str(valuation_id),
            status="pending",
            template_version=request.template_version,
            report_metadata={
                "include_narrative": request.include_narrative,
                "include_comps_grid": request.include_comps_grid,
                "include_photos": request.include_photos,
                "include_charts": request.include_charts,
            },
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)
    else:
        report.status = "pending"
        report.template_version = request.template_version
        report.report_metadata = {
            "include_narrative": request.include_narrative,
            "include_comps_grid": request.include_comps_grid,
            "include_photos": request.include_photos,
            "include_charts": request.include_charts,
        }
        await db.commit()
        await db.refresh(report)

    # Trigger background report generation task
    background_tasks.add_task(generate_report_task, str(valuation_id), report.report_metadata)

    return report


@router.get("/{report_id}/download", response_model=ReportDownloadResponse)
async def download_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # noqa: B008
):
    """Download a generated report PDF."""
    stmt = select(Report).where(Report.id == str(report_id))
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    if report.status != "completed" or not report.minio_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report is not ready for download.",
        )

    # Generate presigned URL from MinIO
    minio_client = get_minio_client()
    settings = get_settings()
    
    try:
        download_url = minio_client.get_presigned_url(
            method="GET",
            bucket_name=settings.minio_bucket,
            object_name=report.minio_path,
            expires=timedelta(hours=1),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate download link: {str(e)}",
        )

    filename = report.minio_path.split("/")[-1]
    return {
        "download_url": download_url,
        "filename": filename,
        "expires_in_seconds": 3600,
    }