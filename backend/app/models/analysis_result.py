"""Analysis result model."""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class AnalysisType(str, enum.Enum):
    """Analysis type."""
    TREND = "trend"
    REGIONAL = "regional"
    COMPETITIVE = "competitive"
    SENTIMENT = "sentiment"
    NLP = "nlp"
    MARKET = "market"


class AnalysisResult(Base):
    """Analysis result model."""

    __tablename__ = "analysis_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_id = Column(UUID(as_uuid=True), ForeignKey("researches.id"), nullable=False)
    analysis_type = Column(Enum(AnalysisType), nullable=False)

    # Results
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    results = Column(JSON, nullable=False)  # Structured analysis results

    # Confidence and metadata
    confidence_score = Column(JSON, nullable=True)  # Confidence scores for different aspects
    data_sources_used = Column(JSON, nullable=True)  # List of source IDs used
    extra_metadata = Column(JSON, nullable=True)  # Additional metadata

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    research = relationship("Research", back_populates="analysis_results")
