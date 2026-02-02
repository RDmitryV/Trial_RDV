"""Collected data model."""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class DataFormat(str, enum.Enum):
    """Data format."""
    HTML = "html"
    JSON = "json"
    XML = "xml"
    TEXT = "text"
    CSV = "csv"
    PDF = "pdf"


class CollectedData(Base):
    """Collected data model."""

    __tablename__ = "collected_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("data_sources.id"), nullable=False)
    research_id = Column(UUID(as_uuid=True), ForeignKey("researches.id"), nullable=True)

    # Data content
    title = Column(String, nullable=True)
    raw_content = Column(Text, nullable=False)
    processed_content = Column(Text, nullable=True)
    format = Column(Enum(DataFormat), default=DataFormat.TEXT, nullable=False)

    # Metadata
    source_url = Column(Text, nullable=True)
    collected_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    content_date = Column(DateTime, nullable=True)  # Date of the actual content
    size_bytes = Column(Integer, nullable=True)

    # Processing metadata
    extra_metadata = Column(JSON, nullable=True)  # Additional metadata as JSON
    is_processed = Column(Enum("yes", "no", name="processed_flag"), default="no", nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    source = relationship("DataSource", back_populates="collected_data")
    research = relationship("Research", back_populates="collected_data")
