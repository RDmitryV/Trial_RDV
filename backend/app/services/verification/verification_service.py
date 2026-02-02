"""Unified verification service."""

from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.data_source import DataSource
from app.models.collected_data import CollectedData
from app.models.source_verification import (
    SourceVerification,
    DataValidation,
    VerificationStatus,
)

from app.services.verification.reliability_assessor import ReliabilityAssessor
from app.services.verification.freshness_checker import FreshnessChecker
from app.services.verification.cross_validator import CrossValidator
from app.services.verification.fact_checker import FactChecker


class VerificationService:
    """Unified service for source and data verification."""

    def __init__(self, db: AsyncSession):
        """Initialize verification service."""
        self.db = db
        self.reliability_assessor = ReliabilityAssessor(db)
        self.freshness_checker = FreshnessChecker(db)
        self.cross_validator = CrossValidator(db)
        self.fact_checker = FactChecker(db)

    async def verify_source(
        self,
        source: DataSource,
        perform_full_check: bool = True,
    ) -> SourceVerification:
        """
        Perform complete verification of a data source.

        Args:
            source: DataSource to verify
            perform_full_check: Whether to perform all checks

        Returns:
            SourceVerification with complete assessment
        """
        # 1. Assess reliability
        verification = await self.reliability_assessor.assess_source(source)

        # If source is blocked, return immediately
        if verification.status == VerificationStatus.FAILED:
            self.db.add(verification)
            await self.db.commit()
            await self.db.refresh(verification)
            return verification

        # 2. Check freshness (if source has been fetched before)
        if source.last_successful_fetch and perform_full_check:
            # Get latest collected data for freshness check
            stmt = select(CollectedData).where(
                CollectedData.source_id == source.id
            ).order_by(CollectedData.collected_date.desc()).limit(1)
            result = await self.db.execute(stmt)
            latest_data = result.scalar_one_or_none()

            if latest_data:
                freshness_result = await self.freshness_checker.check_freshness(
                    latest_data,
                    category=source.category or "general",
                )
                verification = await self.freshness_checker.update_verification_freshness(
                    verification,
                    freshness_result,
                )

        # Save verification
        self.db.add(verification)
        await self.db.commit()
        await self.db.refresh(verification)

        return verification

    async def verify_collected_data(
        self,
        collected_data: CollectedData,
        perform_cross_validation: bool = True,
        perform_fact_check: bool = True,
    ) -> Dict:
        """
        Perform complete verification of collected data.

        Args:
            collected_data: CollectedData to verify
            perform_cross_validation: Whether to cross-validate
            perform_fact_check: Whether to perform fact-checking

        Returns:
            Dictionary with complete verification results
        """
        results = {
            "collected_data_id": str(collected_data.id),
            "verified_at": datetime.utcnow(),
        }

        # 1. Get or create source verification
        source = await self._get_source(collected_data.source_id)
        if source:
            source_verification = await self.verify_source(source, perform_full_check=False)
            results["source_verification"] = {
                "id": str(source_verification.id),
                "status": source_verification.status.value,
                "reliability_score": source_verification.reliability_score,
                "reliability_rating": source_verification.reliability_rating.value if source_verification.reliability_rating else None,
            }

        # 2. Check freshness
        category = source.category if source else "general"
        freshness_result = await self.freshness_checker.check_freshness(
            collected_data,
            category=category,
        )
        results["freshness"] = freshness_result

        # 3. Cross-validation (if requested)
        if perform_cross_validation:
            # Find related data from other sources
            related_data = await self._find_related_data(collected_data)
            validation = await self.cross_validator.validate_data(
                collected_data,
                related_data,
            )
            self.db.add(validation)

            results["cross_validation"] = {
                "id": str(validation.id),
                "is_validated": validation.is_validated,
                "status": validation.validation_status.value,
                "confidence_score": validation.confidence_score,
                "agreement_percentage": validation.agreement_percentage,
                "matching_sources": validation.matching_sources_count,
                "contradicting_sources": validation.contradicting_sources_count,
            }

        # 4. Fact-checking (if requested and source verification exists)
        if perform_fact_check and source_verification:
            fact_check_result = await self.fact_checker.check_facts(
                collected_data,
                source_verification,
            )
            results["fact_check"] = fact_check_result

            # Flag if needed
            source_verification = await self.fact_checker.flag_unverified_data(
                source_verification
            )

        # Commit all changes
        await self.db.commit()

        # 5. Generate overall assessment
        results["overall_assessment"] = self._generate_overall_assessment(results)

        return results

    async def _get_source(self, source_id) -> Optional[DataSource]:
        """Get data source by ID."""
        stmt = select(DataSource).where(DataSource.id == source_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _find_related_data(
        self,
        collected_data: CollectedData,
        limit: int = 10,
    ) -> List[CollectedData]:
        """
        Find related data from other sources for cross-validation.

        Args:
            collected_data: Primary data
            limit: Maximum number of related data to return

        Returns:
            List of related CollectedData
        """
        # Find data from same research but different sources
        stmt = select(CollectedData).where(
            CollectedData.research_id == collected_data.research_id,
            CollectedData.id != collected_data.id,
            CollectedData.source_id != collected_data.source_id,
        ).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def _generate_overall_assessment(self, results: Dict) -> Dict:
        """
        Generate overall assessment based on all verification results.

        Args:
            results: Dictionary with all verification results

        Returns:
            Overall assessment dictionary
        """
        assessment = {
            "reliability": "unknown",
            "is_trustworthy": False,
            "confidence_level": "low",
            "issues": [],
            "warnings": [],
            "recommendations": [],
        }

        # Assess source verification
        if "source_verification" in results:
            source_ver = results["source_verification"]
            reliability_score = source_ver.get("reliability_score", 0)

            if reliability_score >= 0.7:
                assessment["reliability"] = "high"
                assessment["is_trustworthy"] = True
                assessment["confidence_level"] = "high"
            elif reliability_score >= 0.5:
                assessment["reliability"] = "medium"
                assessment["confidence_level"] = "medium"
                assessment["warnings"].append("Source has moderate reliability")
            else:
                assessment["reliability"] = "low"
                assessment["issues"].append("Source has low reliability score")

        # Assess freshness
        if "freshness" in results:
            freshness = results["freshness"]
            if freshness.get("is_outdated"):
                assessment["issues"].append(f"Data is outdated ({freshness.get('days_old')} days old)")
                assessment["recommendations"].append("Consider finding more recent data")

        # Assess cross-validation
        if "cross_validation" in results:
            cross_val = results["cross_validation"]
            if cross_val.get("contradicting_sources", 0) > 0:
                assessment["warnings"].append("Data contradicts other sources")
                assessment["recommendations"].append("Review contradicting sources for accuracy")

            if cross_val.get("confidence_score", 0) >= 0.7:
                assessment["is_trustworthy"] = True
            elif cross_val.get("confidence_score", 0) < 0.5:
                assessment["is_trustworthy"] = False
                assessment["issues"].append("Low confidence from cross-validation")

        # Assess fact-checking
        if "fact_check" in results:
            fact_check = results["fact_check"]
            if not fact_check.get("fact_check_passed"):
                assessment["issues"].append("Failed fact-checking")
                assessment["recommendations"].append("Verify claims against official sources")

        # Determine final confidence level
        if len(assessment["issues"]) == 0 and assessment["is_trustworthy"]:
            assessment["confidence_level"] = "high"
        elif len(assessment["issues"]) > 2:
            assessment["confidence_level"] = "low"
        else:
            assessment["confidence_level"] = "medium"

        return assessment

    async def get_verification_report(
        self,
        source_id: Optional[str] = None,
        collected_data_id: Optional[str] = None,
    ) -> Dict:
        """
        Get comprehensive verification report.

        Args:
            source_id: DataSource ID
            collected_data_id: CollectedData ID

        Returns:
            Verification report dictionary
        """
        report = {
            "generated_at": datetime.utcnow(),
            "source_verifications": [],
            "data_validations": [],
        }

        if source_id:
            stmt = select(SourceVerification).where(
                SourceVerification.source_id == source_id
            )
            result = await self.db.execute(stmt)
            verifications = list(result.scalars().all())

            report["source_verifications"] = [
                {
                    "id": str(v.id),
                    "status": v.status.value,
                    "reliability_score": v.reliability_score,
                    "reliability_rating": v.reliability_rating.value if v.reliability_rating else None,
                    "is_outdated": v.is_outdated,
                    "fact_check_passed": v.fact_check_passed,
                    "verified_at": v.verified_at,
                    "issues_found": v.issues_found,
                }
                for v in verifications
            ]

        if collected_data_id:
            stmt = select(DataValidation).where(
                DataValidation.collected_data_id == collected_data_id
            )
            result = await self.db.execute(stmt)
            validations = list(result.scalars().all())

            report["data_validations"] = [
                {
                    "id": str(v.id),
                    "is_validated": v.is_validated,
                    "status": v.validation_status.value,
                    "confidence_score": v.confidence_score,
                    "agreement_percentage": v.agreement_percentage,
                    "validated_at": v.validated_at,
                }
                for v in validations
            ]

        return report
