"""Report generation API endpoints."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.research import Research
from app.models.report import Report, ReportFormat, ReportStatus
from app.services.report_generation import ReportGenerator
from pydantic import BaseModel


router = APIRouter()


class ReportGenerateRequest(BaseModel):
    """Request model for report generation."""
    research_id: UUID
    format: ReportFormat = ReportFormat.PDF


class ReportResponse(BaseModel):
    """Response model for report."""
    id: UUID
    research_id: UUID
    title: str
    format: ReportFormat
    status: ReportStatus
    file_path: Optional[str]
    file_size: Optional[int]
    error_message: Optional[str]
    created_at: str
    completed_at: Optional[str]

    class Config:
        from_attributes = True


class ReportPreviewResponse(BaseModel):
    """Response model for report preview."""
    title: str
    organization: str
    industry: str
    region: str
    date: str
    sections: List[str]
    estimated_pages: int


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a new report for a research.

    Args:
        request: Report generation request
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Current authenticated user

    Returns:
        Report response with status
    """
    # Check if research exists and belongs to user
    research = db.query(Research).filter(
        Research.id == request.research_id,
        Research.user_id == current_user.id
    ).first()

    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    # Check if research is completed
    if research.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Research must be completed before generating report"
        )

    # Create report generator
    report_generator = ReportGenerator(db)

    # Generate report in background
    report = await report_generator.generate_report(research, request.format)

    return ReportResponse(
        id=report.id,
        research_id=report.research_id,
        title=report.title,
        format=report.format,
        status=report.status,
        file_path=report.file_path,
        file_size=report.file_size,
        error_message=report.error_message,
        created_at=report.created_at.isoformat(),
        completed_at=report.completed_at.isoformat() if report.completed_at else None
    )


@router.get("/preview/{research_id}", response_model=ReportPreviewResponse)
async def get_report_preview(
    research_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a preview of what the report will contain.

    Args:
        research_id: Research ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Report preview
    """
    # Check if research exists and belongs to user
    research = db.query(Research).filter(
        Research.id == research_id,
        Research.user_id == current_user.id
    ).first()

    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    # Create report generator
    report_generator = ReportGenerator(db)

    # Generate preview
    preview = await report_generator.generate_report_preview(research)

    return ReportPreviewResponse(**preview)


@router.get("/list/{research_id}", response_model=List[ReportResponse])
async def list_reports(
    research_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all reports for a research.

    Args:
        research_id: Research ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of reports
    """
    # Check if research exists and belongs to user
    research = db.query(Research).filter(
        Research.id == research_id,
        Research.user_id == current_user.id
    ).first()

    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    # Get all reports for research
    reports = db.query(Report).filter(
        Report.research_id == research_id
    ).order_by(Report.created_at.desc()).all()

    return [
        ReportResponse(
            id=report.id,
            research_id=report.research_id,
            title=report.title,
            format=report.format,
            status=report.status,
            file_path=report.file_path,
            file_size=report.file_size,
            error_message=report.error_message,
            created_at=report.created_at.isoformat(),
            completed_at=report.completed_at.isoformat() if report.completed_at else None
        )
        for report in reports
    ]


@router.get("/download/{report_id}")
async def download_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download a generated report.

    Args:
        report_id: Report ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        File response with report
    """
    # Get report
    report = db.query(Report).filter(Report.id == report_id).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Check if research belongs to user
    research = db.query(Research).filter(
        Research.id == report.research_id,
        Research.user_id == current_user.id
    ).first()

    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    # Check if report is completed
    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Report is not ready for download")

    # Check if file exists
    if not report.file_path or not Path(report.file_path).exists():
        raise HTTPException(status_code=404, detail="Report file not found")

    # Return file
    filename = Path(report.file_path).name
    media_type = "application/pdf" if report.format == ReportFormat.PDF else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    return FileResponse(
        path=report.file_path,
        filename=filename,
        media_type=media_type
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get report details.

    Args:
        report_id: Report ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Report response
    """
    # Get report
    report = db.query(Report).filter(Report.id == report_id).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Check if research belongs to user
    research = db.query(Research).filter(
        Research.id == report.research_id,
        Research.user_id == current_user.id
    ).first()

    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    return ReportResponse(
        id=report.id,
        research_id=report.research_id,
        title=report.title,
        format=report.format,
        status=report.status,
        file_path=report.file_path,
        file_size=report.file_size,
        error_message=report.error_message,
        created_at=report.created_at.isoformat(),
        completed_at=report.completed_at.isoformat() if report.completed_at else None
    )


@router.delete("/{report_id}")
async def delete_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a report.

    Args:
        report_id: Report ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success message
    """
    # Get report
    report = db.query(Report).filter(Report.id == report_id).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Check if research belongs to user
    research = db.query(Research).filter(
        Research.id == report.research_id,
        Research.user_id == current_user.id
    ).first()

    if not research:
        raise HTTPException(status_code=404, detail="Research not found")

    # Delete file if exists
    if report.file_path and Path(report.file_path).exists():
        Path(report.file_path).unlink()

    # Delete report record
    db.delete(report)
    db.commit()

    return {"message": "Report deleted successfully"}
