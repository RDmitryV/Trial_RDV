"""Tests for verification services."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_source import DataSource, SourceType, SourceStatus
from app.models.collected_data import CollectedData, DataFormat
from app.models.source_verification import (
    SourceVerification,
    TrustedSource,
    BlockedSource,
    VerificationStatus,
    ReliabilityRating,
)
from app.services.verification import (
    ReliabilityAssessor,
    FreshnessChecker,
    CrossValidator,
    FactChecker,
    VerificationService,
)


@pytest.mark.asyncio
async def test_reliability_assessor_basic(db_session: AsyncSession):
    """Test basic reliability assessment."""
    # Create a test source
    source = DataSource(
        name="Test News Source",
        source_type=SourceType.NEWS,
        url="https://test-news.com/article",
        reliability_score=0.5,
        success_rate=0.9,
        category="news",
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    # Assess reliability
    assessor = ReliabilityAssessor(db_session)
    verification = await assessor.assess_source(source)

    # Assertions
    assert verification is not None
    assert verification.source_id == source.id
    assert verification.status in [VerificationStatus.VERIFIED, VerificationStatus.FLAGGED, VerificationStatus.FAILED]
    assert verification.reliability_score is not None
    assert 0 <= verification.reliability_score <= 1


@pytest.mark.asyncio
async def test_trusted_source_management(db_session: AsyncSession):
    """Test adding and retrieving trusted sources."""
    assessor = ReliabilityAssessor(db_session)

    # Add a trusted source
    trusted = await assessor.add_trusted_source(
        domain="gov.ru",
        name="Russian Government",
        trust_score=0.95,
        category="government",
        is_official=True,
    )

    assert trusted.domain == "gov.ru"
    assert trusted.trust_score == 0.95
    assert trusted.is_official is True

    # Retrieve trusted sources
    sources = await assessor.get_trusted_sources()
    assert len(sources) == 1
    assert sources[0].domain == "gov.ru"


@pytest.mark.asyncio
async def test_blocked_source_management(db_session: AsyncSession):
    """Test blocking sources."""
    assessor = ReliabilityAssessor(db_session)

    # Block a source
    blocked = await assessor.block_source(
        domain="fake-news.com",
        reason="Unreliable content, multiple fact-check failures",
        is_permanent=True,
    )

    assert blocked.domain == "fake-news.com"
    assert blocked.is_permanent is True

    # Retrieve blocked sources
    sources = await assessor.get_blocked_sources()
    assert len(sources) == 1
    assert sources[0].domain == "fake-news.com"


@pytest.mark.asyncio
async def test_blocked_source_assessment(db_session: AsyncSession):
    """Test that blocked sources get failed verification."""
    # Create and block a source
    source = DataSource(
        name="Fake News Site",
        source_type=SourceType.WEB_SCRAPING,
        url="https://fake-news.com/article",
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    assessor = ReliabilityAssessor(db_session)
    await assessor.block_source(domain="fake-news.com", reason="Test blocking")

    # Assess the blocked source
    verification = await assessor.assess_source(source)

    assert verification.status == VerificationStatus.FAILED
    assert verification.reliability_score == 0.0


@pytest.mark.asyncio
async def test_freshness_checker_recent_data(db_session: AsyncSession):
    """Test freshness checking for recent data."""
    # Create test data with recent date
    collected_data = CollectedData(
        source_id=None,
        raw_content="Test content published today",
        processed_content="Test content published today",
        format=DataFormat.TEXT,
        collected_date=datetime.utcnow(),
        content_date=datetime.utcnow() - timedelta(days=5),
    )
    db_session.add(collected_data)
    await db_session.commit()
    await db_session.refresh(collected_data)

    checker = FreshnessChecker(db_session)
    result = await checker.check_freshness(collected_data, category="news")

    assert result["is_fresh"] is True
    assert result["days_old"] <= 10


@pytest.mark.asyncio
async def test_freshness_checker_outdated_data(db_session: AsyncSession):
    """Test freshness checking for outdated data."""
    # Create test data with old date
    collected_data = CollectedData(
        source_id=None,
        raw_content="Old content",
        processed_content="Old content",
        format=DataFormat.TEXT,
        collected_date=datetime.utcnow(),
        content_date=datetime.utcnow() - timedelta(days=400),
    )
    db_session.add(collected_data)
    await db_session.commit()
    await db_session.refresh(collected_data)

    checker = FreshnessChecker(db_session)
    result = await checker.check_freshness(collected_data, category="news")

    assert result["is_fresh"] is False
    assert result["is_outdated"] is True
    assert result["days_old"] > 90


@pytest.mark.asyncio
async def test_cross_validator_matching_content(db_session: AsyncSession):
    """Test cross-validation with matching content."""
    # Create primary data
    primary_data = CollectedData(
        source_id=None,
        raw_content="The market grew by 15% in 2024",
        processed_content="The market grew by 15% in 2024",
        format=DataFormat.TEXT,
    )

    # Create related data with similar content
    related_data = [
        CollectedData(
            source_id=None,
            raw_content="Market growth reached 15% in 2024",
            processed_content="Market growth reached 15% in 2024",
            format=DataFormat.TEXT,
        ),
        CollectedData(
            source_id=None,
            raw_content="15% market expansion recorded in 2024",
            processed_content="15% market expansion recorded in 2024",
            format=DataFormat.TEXT,
        ),
    ]

    db_session.add_all([primary_data] + related_data)
    await db_session.commit()
    await db_session.refresh(primary_data)

    validator = CrossValidator(db_session)
    validation = await validator.validate_data(primary_data, related_data)

    assert validation.matching_sources_count > 0
    assert validation.is_validated is True


@pytest.mark.asyncio
async def test_fact_checker_citations(db_session: AsyncSession):
    """Test fact checking with citations."""
    # Create verification and data with citations
    source = DataSource(
        name="Test Source",
        source_type=SourceType.NEWS,
        url="https://test.com",
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    verification = SourceVerification(
        source_id=source.id,
        status=VerificationStatus.PENDING,
    )
    db_session.add(verification)
    await db_session.commit()
    await db_session.refresh(verification)

    collected_data = CollectedData(
        source_id=source.id,
        raw_content="According to https://example.com, the data shows growth.",
        processed_content="According to https://example.com, the data shows growth.",
        format=DataFormat.TEXT,
    )
    db_session.add(collected_data)
    await db_session.commit()
    await db_session.refresh(collected_data)

    checker = FactChecker(db_session)
    result = await checker.check_facts(collected_data, verification)

    assert result["fact_check_performed"] is True
    assert "citations" in result


@pytest.mark.asyncio
async def test_verification_service_complete_workflow(db_session: AsyncSession):
    """Test complete verification workflow."""
    # Create a source
    source = DataSource(
        name="Test News Site",
        source_type=SourceType.NEWS,
        url="https://test-news.com",
        success_rate=0.85,
        category="news",
        last_successful_fetch=datetime.utcnow() - timedelta(days=2),
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    # Create collected data
    collected_data = CollectedData(
        source_id=source.id,
        raw_content="Market analysis shows 20% growth",
        processed_content="Market analysis shows 20% growth",
        format=DataFormat.TEXT,
        collected_date=datetime.utcnow(),
        content_date=datetime.utcnow() - timedelta(days=1),
    )
    db_session.add(collected_data)
    await db_session.commit()
    await db_session.refresh(collected_data)

    # Run verification service
    service = VerificationService(db_session)

    # Verify source
    source_verification = await service.verify_source(source)
    assert source_verification is not None
    assert source_verification.reliability_score is not None

    # Verify data
    data_verification = await service.verify_collected_data(
        collected_data,
        perform_cross_validation=False,  # No related data
        perform_fact_check=True,
    )
    assert data_verification is not None
    assert "overall_assessment" in data_verification
    assert "freshness" in data_verification


@pytest.mark.asyncio
async def test_verification_service_report(db_session: AsyncSession):
    """Test verification report generation."""
    # Create and verify a source
    source = DataSource(
        name="Report Test Source",
        source_type=SourceType.API,
        url="https://api.test.com",
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    service = VerificationService(db_session)
    await service.verify_source(source)

    # Get report
    report = await service.get_verification_report(source_id=str(source.id))

    assert report is not None
    assert "source_verifications" in report
    assert len(report["source_verifications"]) > 0
