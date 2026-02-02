"""Cross-validation service for data verification."""

from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import difflib

from app.models.collected_data import CollectedData
from app.models.source_verification import DataValidation, VerificationStatus


class CrossValidator:
    """Service for cross-validating data from multiple sources."""

    def __init__(self, db: AsyncSession):
        """Initialize cross validator."""
        self.db = db
        self.similarity_threshold = 0.7  # Minimum similarity to consider as matching

    async def validate_data(
        self,
        collected_data: CollectedData,
        related_data: List[CollectedData],
    ) -> DataValidation:
        """
        Cross-validate data against related data from other sources.

        Args:
            collected_data: Primary data to validate
            related_data: List of related data from other sources

        Returns:
            DataValidation object with validation results
        """
        if not related_data:
            return await self._create_unvalidated_result(collected_data)

        # Compare content with related data
        comparisons = []
        for related in related_data:
            comparison = self._compare_content(
                collected_data.processed_content or collected_data.raw_content,
                related.processed_content or related.raw_content,
            )
            comparisons.append({
                "source_id": str(related.source_id),
                "similarity": comparison["similarity"],
                "is_matching": comparison["is_matching"],
                "differences": comparison["differences"],
            })

        # Count matching and contradicting sources
        matching = sum(1 for c in comparisons if c["is_matching"])
        contradicting = len(comparisons) - matching

        # Calculate confidence score
        confidence_score = self._calculate_confidence(matching, len(comparisons))

        # Calculate agreement percentage
        agreement_percentage = (matching / len(comparisons) * 100) if comparisons else 0

        # Determine validation status
        is_validated = agreement_percentage >= 50  # At least 50% agreement
        validation_status = self._determine_validation_status(agreement_percentage)

        # Find consensus value
        consensus_value = self._find_consensus(collected_data, related_data)

        # Identify contradictions
        contradictions = [c for c in comparisons if not c["is_matching"]]

        # Create validation record
        validation = DataValidation(
            collected_data_id=collected_data.id,
            is_validated=is_validated,
            validation_status=validation_status,
            matching_sources_count=matching,
            contradicting_sources_count=contradicting,
            consensus_value=consensus_value,
            confidence_score=confidence_score,
            agreement_percentage=agreement_percentage,
            validation_details={
                "total_sources_compared": len(comparisons),
                "comparisons": comparisons,
            },
            contradictions=contradictions if contradictions else None,
            supporting_sources=[c["source_id"] for c in comparisons if c["is_matching"]],
            validated_at=datetime.utcnow() if is_validated else None,
        )

        return validation

    async def _create_unvalidated_result(self, collected_data: CollectedData) -> DataValidation:
        """Create validation result when no related data is available."""
        return DataValidation(
            collected_data_id=collected_data.id,
            is_validated=False,
            validation_status=VerificationStatus.PENDING,
            matching_sources_count=0,
            contradicting_sources_count=0,
            confidence_score=None,
            agreement_percentage=None,
            validation_details={
                "note": "No related data available for cross-validation",
            },
        )

    def _compare_content(self, content1: str, content2: str) -> Dict:
        """
        Compare two pieces of content for similarity.

        Args:
            content1: First content
            content2: Second content

        Returns:
            Dictionary with comparison results
        """
        if not content1 or not content2:
            return {
                "similarity": 0.0,
                "is_matching": False,
                "differences": ["One or both contents are empty"],
            }

        # Calculate similarity ratio
        similarity = difflib.SequenceMatcher(None, content1, content2).ratio()

        # Determine if contents match
        is_matching = similarity >= self.similarity_threshold

        # Find differences if not matching
        differences = []
        if not is_matching:
            # Get detailed diff
            diff = difflib.unified_diff(
                content1.splitlines(keepends=True),
                content2.splitlines(keepends=True),
                n=0,
            )
            differences = [line for line in diff if line.startswith('+') or line.startswith('-')]
            # Limit differences to avoid huge lists
            differences = differences[:50]

        return {
            "similarity": similarity,
            "is_matching": is_matching,
            "differences": differences,
        }

    def _calculate_confidence(self, matching_count: int, total_count: int) -> float:
        """
        Calculate confidence score based on validation results.

        Args:
            matching_count: Number of matching sources
            total_count: Total number of sources compared

        Returns:
            Confidence score (0-1)
        """
        if total_count == 0:
            return 0.0

        # Base confidence from agreement ratio
        agreement_ratio = matching_count / total_count

        # Apply penalties/bonuses
        if total_count == 1:
            # Low confidence with only one comparison
            return agreement_ratio * 0.5
        elif total_count >= 5:
            # High confidence with many comparisons
            return min(1.0, agreement_ratio * 1.2)
        else:
            # Normal confidence
            return agreement_ratio

    def _determine_validation_status(self, agreement_percentage: float) -> VerificationStatus:
        """
        Determine validation status based on agreement percentage.

        Args:
            agreement_percentage: Percentage of sources in agreement

        Returns:
            VerificationStatus enum value
        """
        if agreement_percentage >= 80:
            return VerificationStatus.VERIFIED
        elif agreement_percentage >= 50:
            return VerificationStatus.FLAGGED
        else:
            return VerificationStatus.FAILED

    def _find_consensus(
        self,
        primary_data: CollectedData,
        related_data: List[CollectedData],
    ) -> Optional[str]:
        """
        Find consensus value among data sources.

        Args:
            primary_data: Primary collected data
            related_data: Related data from other sources

        Returns:
            Consensus value or None
        """
        # This is a simplified implementation
        # In a real system, this would use more sophisticated NLP
        # to extract and compare specific claims/facts

        all_content = [primary_data.processed_content or primary_data.raw_content]
        all_content.extend([d.processed_content or d.raw_content for d in related_data if d.processed_content or d.raw_content])

        # Find most common content (simplified)
        # In reality, we'd extract specific facts and find consensus on those
        if not all_content:
            return None

        # For now, return the primary content if it's verified by majority
        return primary_data.processed_content or primary_data.raw_content

    async def find_contradictions(
        self,
        collected_data: CollectedData,
        related_data: List[CollectedData],
    ) -> List[Dict]:
        """
        Find specific contradictions between data sources.

        Args:
            collected_data: Primary data
            related_data: Related data from other sources

        Returns:
            List of contradictions found
        """
        contradictions = []

        for related in related_data:
            comparison = self._compare_content(
                collected_data.processed_content or collected_data.raw_content,
                related.processed_content or related.raw_content,
            )

            if not comparison["is_matching"]:
                contradictions.append({
                    "source_id": str(related.source_id),
                    "similarity": comparison["similarity"],
                    "differences": comparison["differences"][:10],  # Limit to 10
                    "primary_content_snippet": (collected_data.processed_content or collected_data.raw_content)[:200],
                    "contradicting_content_snippet": (related.processed_content or related.raw_content)[:200],
                })

        return contradictions

    async def get_validation_report(
        self,
        collected_data: CollectedData,
    ) -> Dict:
        """
        Get comprehensive validation report for collected data.

        Args:
            collected_data: CollectedData to report on

        Returns:
            Dictionary with validation report
        """
        # Get all validations for this data
        stmt = select(DataValidation).where(
            DataValidation.collected_data_id == collected_data.id
        )
        result = await self.db.execute(stmt)
        validations = list(result.scalars().all())

        if not validations:
            return {
                "has_validation": False,
                "message": "No validation performed yet",
            }

        # Get most recent validation
        latest_validation = max(validations, key=lambda v: v.created_at)

        return {
            "has_validation": True,
            "is_validated": latest_validation.is_validated,
            "status": latest_validation.validation_status.value,
            "confidence_score": latest_validation.confidence_score,
            "agreement_percentage": latest_validation.agreement_percentage,
            "matching_sources": latest_validation.matching_sources_count,
            "contradicting_sources": latest_validation.contradicting_sources_count,
            "has_contradictions": latest_validation.contradicting_sources_count > 0,
            "consensus_value": latest_validation.consensus_value,
            "validated_at": latest_validation.validated_at,
        }

    def set_similarity_threshold(self, threshold: float):
        """
        Set the similarity threshold for matching.

        Args:
            threshold: Similarity threshold (0-1)
        """
        if 0 <= threshold <= 1:
            self.similarity_threshold = threshold
        else:
            raise ValueError("Threshold must be between 0 and 1")

    def get_similarity_threshold(self) -> float:
        """Get the current similarity threshold."""
        return self.similarity_threshold
