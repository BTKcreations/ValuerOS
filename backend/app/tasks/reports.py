"""
ValuerOS — Report Tasks
LLM narrative generation and PDF export.
"""
from __future__ import annotations

from datetime import datetime
import io
import logging
from openai import OpenAI
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.celery_app import celery_app
from app.core.config import get_settings
from app.core.database import get_sync_db
from app.core.storage import get_minio_client
from app.models.models import ComparableSale, Property, Report, Valuation

logger = logging.getLogger(__name__)
settings = get_settings()


def _generate_pdf_report(
    property_obj: Property,
    valuation: Valuation,
    comps: list[ComparableSale],
    narrative: str,
) -> bytes:
    """Generates a beautiful PDF report using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=12,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#4b5563"),
        spaceAfter=24,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=18,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1f2937"),
        spaceAfter=10,
    )

    story = []

    # Title & Header
    story.append(Paragraph("ValuerOS — Real Estate Appraisal Report", title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", subtitle_style))
    story.append(Spacer(1, 12))

    # Property Details Section
    story.append(Paragraph("1. Subject Property Details", heading_style))
    prop_data = [
        [Paragraph("<b>Address:</b>", body_style), Paragraph(f"{property_obj.address_line1}, {property_obj.city}, {property_obj.state} {property_obj.zip_code}", body_style)],
        [Paragraph("<b>Property Type:</b>", body_style), Paragraph(property_obj.property_type.capitalize(), body_style)],
        [Paragraph("<b>Year Built:</b>", body_style), Paragraph(str(property_obj.year_built or "N/A"), body_style)],
        [Paragraph("<b>Gross Building Area:</b>", body_style), Paragraph(f"{property_obj.gross_building_area_sqft:,.0f} sqft" if property_obj.gross_building_area_sqft else "N/A", body_style)],
        [Paragraph("<b>Bedrooms/Bathrooms:</b>", body_style), Paragraph(f"{property_obj.bedrooms or 0} Beds / {property_obj.bathrooms or 0} Baths", body_style)],
    ]
    t_prop = Table(prop_data, colWidths=[150, 350])
    t_prop.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_prop)
    story.append(Spacer(1, 12))

    # Valuation Summary Section
    story.append(Paragraph("2. Valuation Summary", heading_style))
    val_data = [
        [Paragraph("<b>Final Value Estimate:</b>", body_style), Paragraph(f"${valuation.final_value:,.0f}" if valuation.final_value else "N/A", body_style)],
        [Paragraph("<b>Value Range:</b>", body_style), Paragraph(f"${valuation.value_range_low:,.0f} - ${valuation.value_range_high:,.0f}" if valuation.value_range_low else "N/A", body_style)],
        [Paragraph("<b>Confidence Score:</b>", body_style), Paragraph(f"{valuation.confidence_score * 100:.1f}%" if valuation.confidence_score else "N/A", body_style)],
        [Paragraph("<b>Methodology:</b>", body_style), Paragraph(valuation.approach.replace("_", " ").capitalize(), body_style)],
    ]
    t_val = Table(val_data, colWidths=[150, 350])
    t_val.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_val)
    story.append(Spacer(1, 12))

    # Comparable Sales Section
    if comps:
        story.append(Paragraph("3. Comparable Sales Analysis", heading_style))
        comp_headers = [
            Paragraph("<b>Address</b>", body_style),
            Paragraph("<b>Sale Price</b>", body_style),
            Paragraph("<b>GBA (sqft)</b>", body_style),
            Paragraph("<b>Distance</b>", body_style),
        ]
        comp_rows = [comp_headers]
        for comp in comps:
            comp_rows.append([
                Paragraph(comp.address, body_style),
                Paragraph(f"${comp.sale_price:,.0f}" if comp.sale_price else "N/A", body_style),
                Paragraph(f"{comp.gross_building_area_sqft:,.0f}" if comp.gross_building_area_sqft else "N/A", body_style),
                Paragraph(f"{comp.distance_miles:.2f} mi" if comp.distance_miles else "N/A", body_style),
            ])
        t_comps = Table(comp_rows, colWidths=[200, 100, 100, 100])
        t_comps.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t_comps)
        story.append(Spacer(1, 12))

    # Narrative Section
    story.append(Paragraph("4. Appraisal Narrative & Market Analysis", heading_style))
    story.append(Paragraph(narrative.replace("\n", "<br/>"), body_style))

    doc.build(story)
    return buffer.getvalue()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def generate_report(self, valuation_id: str, options: dict | None = None) -> dict:
    """
    Generate a full appraisal report:
    1. LLM narrative generation
    2. PDF composition with ReportLab
    3. Upload to MinIO
    Updates Report.status, narrative, minio_path.
    """
    db = get_sync_db()
    try:
        report = db.query(Report).filter(Report.valuation_id == valuation_id).first()
        if not report:
            return {"status": "error", "message": "Report record not found"}

        valuation = db.query(Valuation).filter(Valuation.id == valuation_id).first()
        if not valuation:
            return {"status": "error", "message": "Valuation not found"}

        property_obj = db.query(Property).filter(Property.id == valuation.property_id).first()
        if not property_obj:
            return {"status": "error", "message": "Property not found"}

        comps = db.query(ComparableSale).filter(ComparableSale.valuation_id == valuation_id).all()

        # 1. Generate Narrative
        narrative = ""
        if settings.openai_api_key:
            client = OpenAI(api_key=settings.openai_api_key)
            prompt = f"""
            You are an expert real estate appraiser.
            Write a professional appraisal narrative and market analysis for the following property:
            Address: {property_obj.address_line1}, {property_obj.city}, {property_obj.state}
            Property Type: {property_obj.property_type}
            Year Built: {property_obj.year_built}
            GBA: {property_obj.gross_building_area_sqft} sqft
            Bedrooms/Bathrooms: {property_obj.bedrooms}/{property_obj.bathrooms}

            The estimated market value is ${valuation.final_value:,.0f} based on {valuation.approach.replace('_', ' ')}.
            
            Provide a concise, professional 2-3 paragraph analysis.
            """
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            narrative = response.choices[0].message.content or ""
        else:
            narrative = (
                f"The subject property located at {property_obj.address_line1} is a well-maintained "
                f"{property_obj.property_type} structure built in {property_obj.year_built or 'N/A'}. "
                f"Based on a comprehensive market analysis using the {valuation.approach.replace('_', ' ')} approach, "
                f"the estimated market value of the property is ${valuation.final_value:,.0f} as of the effective date. "
                f"This estimate is supported by recent comparable sales in the immediate submarket, adjusted for "
                f"differences in size, condition, and utility."
            )

        # 2. Generate PDF
        pdf_bytes = _generate_pdf_report(property_obj, valuation, comps, narrative)

        # 3. Upload to MinIO
        minio_client = get_minio_client()
        minio_path = f"reports/{valuation_id}/appraisal_report.pdf"
        
        minio_client.put_object(
            bucket_name=settings.minio_bucket,
            object_name=minio_path,
            data=io.BytesIO(pdf_bytes),
            length=len(pdf_bytes),
            content_type="application/pdf",
        )

        # 4. Update Report record
        report.status = "completed"
        report.narrative = narrative
        report.minio_path = minio_path
        db.commit()

        return {
            "valuation_id": valuation_id,
            "status": "completed",
            "minio_path": minio_path,
        }
    except Exception as exc:
        db.rollback()
        logger.error(f"Error in generate_report: {str(exc)}")
        raise self.retry(exc=exc)
    finally:
        db.close()