"""Source reliability assessment service."""

from typing import Optional, Dict, List
from datetime import datetime
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.data_source import DataSource, SourceStatus
from app.models.source_verification import (
    SourceVerification,
    TrustedSource,
    BlockedSource,
    VerificationStatus,
    ReliabilityRating,
)


class ReliabilityAssessor:
    """Service for assessing source reliability."""

    def __init__(self, db: AsyncSession):
        """Initialize reliability assessor."""
        self.db = db

        # Weight factors for reliability score calculation
        self.weights = {
            "domain_trust": 0.35,  # Trust based on domain reputation
            "success_rate": 0.25,  # Historical success rate
            "freshness": 0.20,  # How recent the data is
            "content_quality": 0.15,  # Quality of content
            "cross_validation": 0.05,  # Validation against other sources
        }

    async def assess_source(self, source: DataSource) -> SourceVerification:
        """
        Assess the reliability of a data source.

        Args:
            source: DataSource to assess

        Returns:
            SourceVerification object with assessment results
        """
        # Check if source is in blacklist
        is_blocked = await self._is_source_blocked(source)
        if is_blocked:
            return await self._create_blocked_verification(source)

        # Calculate individual scores
        domain_trust_score = await self._calculate_domain_trust(source)
        success_rate_score = self._calculate_success_rate(source)
        freshness_score = self._calculate_freshness_score(source)
        content_quality_score = await self._calculate_content_quality(source)

        # Calculate overall reliability score
        reliability_score = (
            domain_trust_score * self.weights["domain_trust"]
            + success_rate_score * self.weights["success_rate"]
            + freshness_score * self.weights["freshness"]
            + content_quality_score * self.weights["content_quality"]
        )

        # Determine reliability rating
        reliability_rating = self._get_reliability_rating(reliability_score)

        # Determine verification status
        status = self._determine_verification_status(reliability_score)

        # Create verification record
        verification = SourceVerification(
            source_id=source.id,
            status=status,
            reliability_rating=reliability_rating,
            reliability_score=reliability_score,
            trustworthiness_score=domain_trust_score,
            content_quality_score=content_quality_score,
            last_update_check=datetime.utcnow(),
            verified_at=datetime.utcnow() if status == VerificationStatus.VERIFIED else None,
            verification_metadata={
                "domain_trust_score": domain_trust_score,
                "success_rate_score": success_rate_score,
                "freshness_score": freshness_score,
                "content_quality_score": content_quality_score,
            },
        )

        # Update source reliability score
        source.reliability_score = reliability_score

        return verification

    async def _is_source_blocked(self, source: DataSource) -> bool:
        """Check if source domain is in blacklist."""
        if not source.url:
            return False

        domain = self._extract_domain(source.url)
        stmt = select(BlockedSource).where(BlockedSource.domain == domain)
        result = await self.db.execute(stmt)
        blocked = result.scalar_one_or_none()

        return blocked is not None

    async def _create_blocked_verification(self, source: DataSource) -> SourceVerification:
        """Create verification record for blocked source."""
        domain = self._extract_domain(source.url) if source.url else "unknown"

        # Get block reason
        stmt = select(BlockedSource).where(BlockedSource.domain == domain)
        result = await self.db.execute(stmt)
        blocked = result.scalar_one_or_none()

        verification = SourceVerification(
            source_id=source.id,
            status=VerificationStatus.FAILED,
            reliability_rating=ReliabilityRating.UNRELIABLE,
            reliability_score=0.0,
            trustworthiness_score=0.0,
            last_update_check=datetime.utcnow(),
            verification_notes=f"Source is in blacklist: {blocked.reason if blocked else 'Unknown reason'}",
            issues_found=["blocked_source"],
        )

        # Update source status
        source.reliability_score = 0.0
        source.status = SourceStatus.FAILED

        return verification

    async def _calculate_domain_trust(self, source: DataSource) -> float:
        """
        Calculate trust score based on domain reputation.

        Returns:
            Trust score (0-1)
        """
        if not source.url:
            return 0.5  # Neutral score for sources without URL

        domain = self._extract_domain(source.url)

        # Check if domain is in trusted sources
        stmt = select(TrustedSource).where(TrustedSource.domain == domain)
        result = await self.db.execute(stmt)
        trusted = result.scalar_one_or_none()

        if trusted:
            return trusted.trust_score

        # Domain heuristics for Russian sources
        if self._is_government_domain(domain):
            return 0.95
        elif self._is_educational_domain(domain):
            return 0.85
        elif self._is_research_domain(domain):
            return 0.80
        elif self._is_news_domain(domain):
            return 0.60
        else:
            return 0.50  # Unknown domain, neutral score

    def _calculate_success_rate(self, source: DataSource) -> float:
        """
        Calculate score based on historical success rate.

        Returns:
            Success rate score (0-1)
        """
        return source.success_rate if source.success_rate is not None else 0.5

    def _calculate_freshness_score(self, source: DataSource) -> float:
        """
        Calculate score based on data freshness.

        Returns:
            Freshness score (0-1)
        """
        if not source.last_successful_fetch:
            return 0.5  # Neutral for new sources

        days_since_fetch = (datetime.utcnow() - source.last_successful_fetch).days

        # Score decreases as data gets older
        if days_since_fetch <= 1:
            return 1.0
        elif days_since_fetch <= 7:
            return 0.9
        elif days_since_fetch <= 30:
            return 0.7
        elif days_since_fetch <= 90:
            return 0.5
        elif days_since_fetch <= 180:
            return 0.3
        else:
            return 0.1

    async def _calculate_content_quality(self, source: DataSource) -> float:
        """
        Calculate score based on content quality.

        Returns:
            Content quality score (0-1)
        """
        # This is a placeholder - in real implementation, this would analyze
        # the actual content quality using NLP techniques
        # For now, we use source type as a proxy

        score = 0.5  # Default neutral score

        if source.source_type.value == "government":
            score = 0.9
        elif source.source_type.value == "api":
            score = 0.85
        elif source.source_type.value == "database":
            score = 0.8
        elif source.source_type.value == "news":
            score = 0.6
        elif source.source_type.value == "web_scraping":
            score = 0.5

        return score

    def _get_reliability_rating(self, score: float) -> ReliabilityRating:
        """
        Convert reliability score to rating category.

        Args:
            score: Reliability score (0-1)

        Returns:
            ReliabilityRating enum value
        """
        if score >= 0.9:
            return ReliabilityRating.EXCELLENT
        elif score >= 0.7:
            return ReliabilityRating.GOOD
        elif score >= 0.5:
            return ReliabilityRating.FAIR
        elif score >= 0.3:
            return ReliabilityRating.POOR
        else:
            return ReliabilityRating.UNRELIABLE

    def _determine_verification_status(self, score: float) -> VerificationStatus:
        """
        Determine verification status based on score.

        Args:
            score: Reliability score (0-1)

        Returns:
            VerificationStatus enum value
        """
        if score >= 0.7:
            return VerificationStatus.VERIFIED
        elif score >= 0.5:
            return VerificationStatus.FLAGGED
        else:
            return VerificationStatus.FAILED

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc

    def _is_government_domain(self, domain: str) -> bool:
        """Check if domain is a government domain."""
        gov_indicators = [".gov.ru", ".ru/gov", "gosuslugi", "government"]
        return any(indicator in domain.lower() for indicator in gov_indicators)

    def _is_educational_domain(self, domain: str) -> bool:
        """Check if domain is an educational domain."""
        edu_indicators = [".edu", ".ac.ru", "university", "institut"]
        return any(indicator in domain.lower() for indicator in edu_indicators)

    def _is_research_domain(self, domain: str) -> bool:
        """Check if domain is a research domain."""
        research_indicators = ["research", "scholar", "science", "academic", "nih.gov"]
        return any(indicator in domain.lower() for indicator in research_indicators)

    def _is_news_domain(self, domain: str) -> bool:
        """Check if domain is a news domain."""
        news_indicators = ["news", "tass", "interfax", "ria", "rbc", "kommersant"]
        return any(indicator in domain.lower() for indicator in news_indicators)

    async def add_trusted_source(
        self,
        domain: str,
        name: str,
        trust_score: float = 1.0,
        category: Optional[str] = None,
        description: Optional[str] = None,
        is_official: bool = False,
    ) -> TrustedSource:
        """
        Add a domain to the trusted sources list.

        Args:
            domain: Domain name
            name: Source name
            trust_score: Trust score (0-1)
            category: Source category
            description: Description of the source
            is_official: Whether it's an official source

        Returns:
            TrustedSource object
        """
        trusted_source = TrustedSource(
            domain=domain,
            name=name,
            trust_score=trust_score,
            category=category,
            description=description,
            is_official=is_official,
        )

        self.db.add(trusted_source)
        await self.db.commit()
        await self.db.refresh(trusted_source)

        return trusted_source

    async def block_source(
        self,
        domain: str,
        reason: str,
        blocked_by: Optional[str] = None,
        is_permanent: bool = False,
    ) -> BlockedSource:
        """
        Add a domain to the blocked sources list.

        Args:
            domain: Domain name
            reason: Reason for blocking
            blocked_by: Who blocked the source
            is_permanent: Whether the block is permanent

        Returns:
            BlockedSource object
        """
        blocked_source = BlockedSource(
            domain=domain,
            reason=reason,
            blocked_by=blocked_by,
            is_permanent=is_permanent,
        )

        self.db.add(blocked_source)
        await self.db.commit()
        await self.db.refresh(blocked_source)

        return blocked_source

    async def get_trusted_sources(self) -> List[TrustedSource]:
        """Get all trusted sources."""
        stmt = select(TrustedSource)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_blocked_sources(self) -> List[BlockedSource]:
        """Get all blocked sources."""
        stmt = select(BlockedSource)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
