"""API endpoints for source verification."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.data_source import DataSource
from app.models.collected_data import CollectedData
from app.models.source_verification import (
    SourceVerification,
    TrustedSource,
    BlockedSource,
    DataValidation,
    VerificationStatus,
    ReliabilityRating,
)
from app.services.verification import VerificationService

router = APIRouter(prefix="/verification", tags=["verification"])


# Pydantic schemas for requests and responses
class SourceVerificationResponse(BaseModel):
    """Source verification response schema."""
    id: str
    source_id: str
    status: str
    reliability_rating: Optional[str]
    reliability_score: Optional[float]
    is_outdated: bool
    fact_check_performed: bool
    fact_check_passed: Optional[bool]
    verified_at: Optional[str]
    issues_found: Optional[List[str]]

    class Config:
        from_attributes = True


class DataVerificationResponse(BaseModel):
    """Data verification response schema."""
    collected_data_id: str
    source_verification: Optional[dict]
    freshness: dict
    cross_validation: Optional[dict]
    fact_check: Optional[dict]
    overall_assessment: dict


class TrustedSourceCreate(BaseModel):
    """Schema for creating a trusted source."""
    domain: str
    name: str
    trust_score: float = Field(default=1.0, ge=0.0, le=1.0)
    category: Optional[str] = None
    description: Optional[str] = None
    is_official: bool = False


class TrustedSourceResponse(BaseModel):
    """Trusted source response schema."""
    id: str
    domain: str
    name: str
    trust_score: float
    category: Optional[str]
    is_official: bool

    class Config:
        from_attributes = True


class BlockedSourceCreate(BaseModel):
    """Schema for creating a blocked source."""
    domain: str
    reason: str
    blocked_by: Optional[str] = None
    is_permanent: bool = False


class BlockedSourceResponse(BaseModel):
    """Blocked source response schema."""
    id: str
    domain: str
    reason: str
    is_permanent: bool
    blocked_by: Optional[str]

    class Config:
        from_attributes = True


@router.post("/sources/{source_id}/verify", response_model=SourceVerificationResponse)
async def verify_source(
    source_id: UUID,
    perform_full_check: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify a data source.

    Performs comprehensive verification including reliability assessment,
    freshness checking, and other quality checks.
    """
    # Get source
    stmt = select(DataSource).where(DataSource.id == source_id)
    result = await db.execute(stmt)
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_id} not found",
        )

    # Verify source
    verification_service = VerificationService(db)
    verification = await verification_service.verify_source(source, perform_full_check)

    return SourceVerificationResponse(
        id=str(verification.id),
        source_id=str(verification.source_id),
        status=verification.status.value,
        reliability_rating=verification.reliability_rating.value if verification.reliability_rating else None,
        reliability_score=verification.reliability_score,
        is_outdated=verification.is_outdated,
        fact_check_performed=verification.fact_check_performed,
        fact_check_passed=verification.fact_check_passed,
        verified_at=verification.verified_at.isoformat() if verification.verified_at else None,
        issues_found=verification.issues_found,
    )


@router.post("/data/{collected_data_id}/verify", response_model=DataVerificationResponse)
async def verify_collected_data(
    collected_data_id: UUID,
    perform_cross_validation: bool = True,
    perform_fact_check: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify collected data.

    Performs comprehensive verification including source verification,
    freshness checking, cross-validation, and fact-checking.
    """
    # Get collected data
    stmt = select(CollectedData).where(CollectedData.id == collected_data_id)
    result = await db.execute(stmt)
    collected_data = result.scalar_one_or_none()

    if not collected_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collected data {collected_data_id} not found",
        )

    # Verify data
    verification_service = VerificationService(db)
    verification_result = await verification_service.verify_collected_data(
        collected_data,
        perform_cross_validation=perform_cross_validation,
        perform_fact_check=perform_fact_check,
    )

    return DataVerificationResponse(**verification_result)


@router.get("/sources/{source_id}/verifications", response_model=List[SourceVerificationResponse])
async def get_source_verifications(
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all verifications for a source."""
    stmt = select(SourceVerification).where(SourceVerification.source_id == source_id)
    result = await db.execute(stmt)
    verifications = result.scalars().all()

    return [
        SourceVerificationResponse(
            id=str(v.id),
            source_id=str(v.source_id),
            status=v.status.value,
            reliability_rating=v.reliability_rating.value if v.reliability_rating else None,
            reliability_score=v.reliability_score,
            is_outdated=v.is_outdated,
            fact_check_performed=v.fact_check_performed,
            fact_check_passed=v.fact_check_passed,
            verified_at=v.verified_at.isoformat() if v.verified_at else None,
            issues_found=v.issues_found,
        )
        for v in verifications
    ]


@router.get("/report")
async def get_verification_report(
    source_id: Optional[UUID] = None,
    collected_data_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive verification report."""
    if not source_id and not collected_data_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either source_id or collected_data_id must be provided",
        )

    verification_service = VerificationService(db)
    report = await verification_service.get_verification_report(
        source_id=str(source_id) if source_id else None,
        collected_data_id=str(collected_data_id) if collected_data_id else None,
    )

    return report


# Trusted sources endpoints
@router.post("/trusted-sources", response_model=TrustedSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_trusted_source(
    source: TrustedSourceCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a domain to the trusted sources list."""
    from app.services.verification.reliability_assessor import ReliabilityAssessor

    assessor = ReliabilityAssessor(db)
    trusted_source = await assessor.add_trusted_source(
        domain=source.domain,
        name=source.name,
        trust_score=source.trust_score,
        category=source.category,
        description=source.description,
        is_official=source.is_official,
    )

    return TrustedSourceResponse(
        id=str(trusted_source.id),
        domain=trusted_source.domain,
        name=trusted_source.name,
        trust_score=trusted_source.trust_score,
        category=trusted_source.category,
        is_official=trusted_source.is_official,
    )


@router.get("/trusted-sources", response_model=List[TrustedSourceResponse])
async def list_trusted_sources(
    db: AsyncSession = Depends(get_db),
):
    """Get all trusted sources."""
    from app.services.verification.reliability_assessor import ReliabilityAssessor

    assessor = ReliabilityAssessor(db)
    sources = await assessor.get_trusted_sources()

    return [
        TrustedSourceResponse(
            id=str(s.id),
            domain=s.domain,
            name=s.name,
            trust_score=s.trust_score,
            category=s.category,
            is_official=s.is_official,
        )
        for s in sources
    ]


# Blocked sources endpoints
@router.post("/blocked-sources", response_model=BlockedSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_blocked_source(
    source: BlockedSourceCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a domain to the blocked sources list."""
    from app.services.verification.reliability_assessor import ReliabilityAssessor

    assessor = ReliabilityAssessor(db)
    blocked_source = await assessor.block_source(
        domain=source.domain,
        reason=source.reason,
        blocked_by=source.blocked_by,
        is_permanent=source.is_permanent,
    )

    return BlockedSourceResponse(
        id=str(blocked_source.id),
        domain=blocked_source.domain,
        reason=blocked_source.reason,
        is_permanent=blocked_source.is_permanent,
        blocked_by=blocked_source.blocked_by,
    )


@router.get("/blocked-sources", response_model=List[BlockedSourceResponse])
async def list_blocked_sources(
    db: AsyncSession = Depends(get_db),
):
    """Get all blocked sources."""
    from app.services.verification.reliability_assessor import ReliabilityAssessor

    assessor = ReliabilityAssessor(db)
    sources = await assessor.get_blocked_sources()

    return [
        BlockedSourceResponse(
            id=str(s.id),
            domain=s.domain,
            reason=s.reason,
            is_permanent=s.is_permanent,
            blocked_by=s.blocked_by,
        )
        for s in sources
    ]
