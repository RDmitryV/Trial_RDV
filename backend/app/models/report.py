"""Report model."""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class ReportFormat(str, enum.Enum):
    """Report format."""
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"


class ReportStatus(str, enum.Enum):
    """Report status."""
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Report(Base):
    """Report model."""

    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_id = Column(UUID(as_uuid=True), ForeignKey("researches.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(JSON, nullable=True)  # Structured report content
    format = Column(Enum(ReportFormat), default=ReportFormat.PDF, nullable=False)
    file_path = Column(String, nullable=True)  # Path to generated file
    file_size = Column(Integer, nullable=True)  # File size in bytes
    status = Column(Enum(ReportStatus), default=ReportStatus.GENERATING, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    research = relationship("Research", back_populates="reports")
