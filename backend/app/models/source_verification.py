"""Source verification models."""

from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey, Enum, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class VerificationStatus(str, enum.Enum):
    """Verification status."""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    FLAGGED = "flagged"  # Спорные данные
    OUTDATED = "outdated"


class ReliabilityRating(str, enum.Enum):
    """Source reliability rating."""
    EXCELLENT = "excellent"  # 0.9-1.0
    GOOD = "good"  # 0.7-0.89
    FAIR = "fair"  # 0.5-0.69
    POOR = "poor"  # 0.3-0.49
    UNRELIABLE = "unreliable"  # 0.0-0.29


class SourceVerification(Base):
    """Source verification results."""

    __tablename__ = "source_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("data_sources.id"), nullable=False)

    # Verification status
    status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING, nullable=False)
    reliability_rating = Column(Enum(ReliabilityRating), nullable=True)

    # Reliability metrics
    reliability_score = Column(Float, nullable=True)  # 0-1 scale
    trustworthiness_score = Column(Float, nullable=True)  # Based on domain reputation
    content_quality_score = Column(Float, nullable=True)  # Content analysis score

    # Freshness check
    last_update_check = Column(DateTime, nullable=True)
    content_date = Column(DateTime, nullable=True)  # Date of the content
    is_outdated = Column(Boolean, default=False, nullable=False)
    days_since_update = Column(Float, nullable=True)

    # Cross-validation
    cross_validation_count = Column(Float, default=0, nullable=False)  # Number of sources compared
    consensus_score = Column(Float, nullable=True)  # Agreement with other sources
    has_contradictions = Column(Boolean, default=False, nullable=False)

    # Fact-checking
    fact_check_performed = Column(Boolean, default=False, nullable=False)
    fact_check_passed = Column(Boolean, nullable=True)
    verified_claims = Column(Float, default=0, nullable=False)
    total_claims = Column(Float, default=0, nullable=False)

    # Details
    verification_notes = Column(Text, nullable=True)
    issues_found = Column(JSON, nullable=True)  # List of issues detected
    verification_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    verified_at = Column(DateTime, nullable=True)

    # Relationships
    source = relationship("DataSource", backref="verifications")


class TrustedSource(Base):
    """Whitelist of trusted sources."""

    __tablename__ = "trusted_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)  # e.g., "government", "academic", "news"

    # Trust metrics
    trust_score = Column(Float, default=1.0, nullable=False)  # 0-1 scale
    is_official = Column(Boolean, default=False, nullable=False)  # Official government/organization

    # Metadata
    country = Column(String, nullable=True)
    language = Column(String, default="ru", nullable=False)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class BlockedSource(Base):
    """Blacklist of unreliable sources."""

    __tablename__ = "blocked_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain = Column(String, nullable=False, unique=True)
    reason = Column(Text, nullable=False)
    blocked_by = Column(String, nullable=True)  # Who blocked it

    # Metadata
    is_permanent = Column(Boolean, default=False, nullable=False)
    unblock_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class DataValidation(Base):
    """Cross-validation results for collected data."""

    __tablename__ = "data_validations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collected_data_id = Column(UUID(as_uuid=True), ForeignKey("collected_data.id"), nullable=False)

    # Validation results
    is_validated = Column(Boolean, default=False, nullable=False)
    validation_status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING, nullable=False)

    # Cross-validation
    matching_sources_count = Column(Float, default=0, nullable=False)
    contradicting_sources_count = Column(Float, default=0, nullable=False)
    consensus_value = Column(Text, nullable=True)

    # Confidence metrics
    confidence_score = Column(Float, nullable=True)  # 0-1 scale
    agreement_percentage = Column(Float, nullable=True)  # % of sources agreeing

    # Details
    validation_details = Column(JSON, nullable=True)
    contradictions = Column(JSON, nullable=True)  # List of contradicting data
    supporting_sources = Column(JSON, nullable=True)  # List of supporting source IDs

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    validated_at = Column(DateTime, nullable=True)

    # Relationships
    collected_data = relationship("CollectedData", backref="validations")
