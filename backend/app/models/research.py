"""Research model."""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class ResearchStatus(str, enum.Enum):
    """Research status."""
    CREATED = "created"
    COLLECTING_DATA = "collecting_data"
    ANALYZING = "analyzing"
    GENERATING_REPORT = "generating_report"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchType(str, enum.Enum):
    """Research type."""
    MARKET = "market"
    COMPETITOR = "competitor"
    REGIONAL = "regional"
    TARGET_AUDIENCE = "target_audience"
    TREND = "trend"


class Research(Base):
    """Research model."""

    __tablename__ = "researches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    product_description = Column(Text, nullable=False)
    industry = Column(String, nullable=False)
    region = Column(String, nullable=False)
    research_type = Column(Enum(ResearchType), default=ResearchType.MARKET, nullable=False)
    additional_params = Column(JSON, nullable=True)
    status = Column(Enum(ResearchStatus), default=ResearchStatus.CREATED, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="researches")
    reports = relationship("Report", back_populates="research", cascade="all, delete-orphan")
