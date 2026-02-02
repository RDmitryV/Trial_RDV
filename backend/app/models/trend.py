"""Trend model."""

from sqlalchemy import Column, String, Text, DateTime, Float, Enum, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class TrendSignificance(str, enum.Enum):
    """Trend significance level."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TrendDirection(str, enum.Enum):
    """Trend direction."""
    GROWING = "growing"
    DECLINING = "declining"
    STABLE = "stable"
    EMERGING = "emerging"


class Trend(Base):
    """Trend model."""

    __tablename__ = "trends"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Trend identification
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    industry = Column(String, nullable=False)
    category = Column(String, nullable=True)

    # Trend metrics
    significance = Column(Enum(TrendSignificance), default=TrendSignificance.MEDIUM, nullable=False)
    direction = Column(Enum(TrendDirection), nullable=False)
    confidence_score = Column(Float, default=0.5, nullable=False)  # 0-1 scale
    momentum = Column(Float, nullable=True)  # Rate of change

    # Temporal data
    first_observed = Column(DateTime, nullable=False)
    last_observed = Column(DateTime, nullable=False)
    peak_date = Column(DateTime, nullable=True)

    # Related data
    related_keywords = Column(JSON, nullable=True)  # List of related keywords
    related_industries = Column(JSON, nullable=True)  # Cross-industry connections
    evidence = Column(JSON, nullable=True)  # Supporting evidence (sources, mentions, etc.)

    # Metadata
    extra_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_trend_industry', 'industry'),
        Index('idx_trend_significance', 'significance'),
        Index('idx_trend_dates', 'first_observed', 'last_observed'),
    )
