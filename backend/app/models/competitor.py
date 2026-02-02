"""Competitor model."""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Competitor(Base):
    """Competitor model."""

    __tablename__ = "competitors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_id = Column(UUID(as_uuid=True), ForeignKey("researches.id"), nullable=False)

    # Basic information
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    website = Column(String, nullable=True)
    industry = Column(String, nullable=False)
    region = Column(String, nullable=True)

    # Market position
    market_share = Column(Float, nullable=True)  # Percentage
    positioning = Column(Text, nullable=True)
    target_audience = Column(Text, nullable=True)

    # SWOT Analysis
    strengths = Column(JSON, nullable=True)  # List of strengths
    weaknesses = Column(JSON, nullable=True)  # List of weaknesses
    opportunities = Column(JSON, nullable=True)  # List of opportunities
    threats = Column(JSON, nullable=True)  # List of threats

    # Competitive metrics
    competitive_advantage = Column(Text, nullable=True)
    price_positioning = Column(String, nullable=True)  # e.g., "premium", "mid-market", "budget"
    key_products = Column(JSON, nullable=True)  # List of key products/services

    # Analysis data
    similarity_score = Column(Float, nullable=True)  # Similarity to our product (0-1)
    threat_level = Column(Float, nullable=True)  # Threat level (0-1)
    extra_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    research = relationship("Research", back_populates="competitors")
