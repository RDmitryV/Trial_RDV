"""Data freshness checking service."""

from typing import Optional, Dict
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import re
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collected_data import CollectedData
from app.models.source_verification import SourceVerification, VerificationStatus


class FreshnessChecker:
    """Service for checking data freshness and actuality."""

    def __init__(self, db: AsyncSession):
        """Initialize freshness checker."""
        self.db = db

        # Freshness thresholds (in days) by content category
        self.freshness_thresholds = {
            "market_data": 30,  # Market data should be within 30 days
            "news": 90,  # News within 90 days
            "statistics": 365,  # Official statistics within 1 year
            "research": 730,  # Research papers within 2 years
            "general": 180,  # General content within 6 months
        }

    async def check_freshness(
        self,
        collected_data: CollectedData,
        category: str = "general",
    ) -> Dict:
        """
        Check if collected data is fresh/up-to-date.

        Args:
            collected_data: CollectedData to check
            category: Content category for threshold determination

        Returns:
            Dictionary with freshness check results
        """
        # Extract content date from the collected data
        content_date = await self._extract_content_date(collected_data)

        if not content_date:
            return {
                "is_fresh": None,
                "content_date": None,
                "days_old": None,
                "threshold_days": self.freshness_thresholds.get(category, 180),
                "warning": "Unable to determine content date",
            }

        # Calculate age
        days_old = (datetime.utcnow() - content_date).days

        # Get threshold for category
        threshold = self.freshness_thresholds.get(category, 180)

        # Determine if data is fresh
        is_fresh = days_old <= threshold

        result = {
            "is_fresh": is_fresh,
            "content_date": content_date,
            "days_old": days_old,
            "threshold_days": threshold,
            "is_outdated": not is_fresh,
            "freshness_score": self._calculate_freshness_score(days_old, threshold),
        }

        # Add warning if outdated
        if not is_fresh:
            result["warning"] = f"Data is {days_old} days old, exceeds threshold of {threshold} days"

        return result

    async def _extract_content_date(self, collected_data: CollectedData) -> Optional[datetime]:
        """
        Extract content publication date from collected data.

        Args:
            collected_data: CollectedData object

        Returns:
            Content date or None if not found
        """
        # First check if content_date is already set
        if collected_data.content_date:
            return collected_data.content_date

        # Try to extract from metadata
        if collected_data.extra_metadata and isinstance(collected_data.extra_metadata, dict):
            if "publication_date" in collected_data.extra_metadata:
                return self._parse_date(collected_data.extra_metadata["publication_date"])
            if "date" in collected_data.extra_metadata:
                return self._parse_date(collected_data.extra_metadata["date"])

        # Try to extract from content
        content_date = self._extract_date_from_text(
            collected_data.processed_content or collected_data.raw_content
        )

        if content_date:
            return content_date

        # Fallback to collection date as last resort
        return collected_data.collected_date

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string to datetime.

        Args:
            date_str: Date string in various formats

        Returns:
            datetime object or None
        """
        if not date_str:
            return None

        try:
            # Try using dateutil parser (handles many formats)
            return date_parser.parse(date_str, fuzzy=True)
        except (ValueError, TypeError):
            return None

    def _extract_date_from_text(self, text: str) -> Optional[datetime]:
        """
        Extract date from text content using patterns.

        Args:
            text: Text content

        Returns:
            datetime object or None
        """
        if not text:
            return None

        # Common date patterns
        patterns = [
            # ISO format: 2024-01-15
            r'\b(\d{4})-(\d{2})-(\d{2})\b',
            # Russian format: 15.01.2024
            r'\b(\d{2})\.(\d{2})\.(\d{4})\b',
            # Russian month names
            r'\b(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(\d{4})\b',
        ]

        months_ru = {
            'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
            'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
            'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
        }

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                match = matches[0]  # Take first match
                try:
                    if isinstance(match, tuple) and len(match) == 3:
                        if match[1] in months_ru:
                            # Russian month name format
                            day = int(match[0])
                            month = months_ru[match[1]]
                            year = int(match[2])
                            return datetime(year, month, day)
                        elif '-' in text[text.find(match[0]):text.find(match[0])+15]:
                            # ISO format
                            year = int(match[0])
                            month = int(match[1])
                            day = int(match[2])
                            return datetime(year, month, day)
                        else:
                            # Russian DD.MM.YYYY format
                            day = int(match[0])
                            month = int(match[1])
                            year = int(match[2])
                            return datetime(year, month, day)
                except (ValueError, IndexError):
                    continue

        return None

    def _calculate_freshness_score(self, days_old: int, threshold: int) -> float:
        """
        Calculate freshness score (0-1).

        Args:
            days_old: Age of content in days
            threshold: Threshold for freshness

        Returns:
            Freshness score (0-1), where 1 is very fresh
        """
        if days_old <= 0:
            return 1.0

        if days_old >= threshold * 2:
            return 0.0

        # Linear decay from 1.0 to 0.0
        score = 1.0 - (days_old / (threshold * 2))
        return max(0.0, min(1.0, score))

    async def check_for_updates(self, collected_data: CollectedData) -> Dict:
        """
        Check if there are updates available for the content.

        Args:
            collected_data: CollectedData to check

        Returns:
            Dictionary with update check results
        """
        # This would typically involve re-fetching the URL and comparing
        # For now, we return a placeholder result

        return {
            "has_updates": False,
            "last_checked": datetime.utcnow(),
            "update_available": False,
            "note": "Update checking not yet implemented",
        }

    async def update_verification_freshness(
        self,
        verification: SourceVerification,
        freshness_result: Dict,
    ) -> SourceVerification:
        """
        Update verification record with freshness check results.

        Args:
            verification: SourceVerification to update
            freshness_result: Results from check_freshness

        Returns:
            Updated SourceVerification
        """
        verification.last_update_check = datetime.utcnow()
        verification.content_date = freshness_result.get("content_date")
        verification.is_outdated = freshness_result.get("is_outdated", False)
        verification.days_since_update = freshness_result.get("days_old")

        # Add freshness issues if outdated
        if freshness_result.get("is_outdated"):
            issues = verification.issues_found or []
            if "outdated_content" not in issues:
                issues.append("outdated_content")
            verification.issues_found = issues

            # Update verification status if it was verified
            if verification.status == VerificationStatus.VERIFIED:
                verification.status = VerificationStatus.FLAGGED

        # Update metadata
        if not verification.verification_metadata:
            verification.verification_metadata = {}
        verification.verification_metadata["freshness_check"] = freshness_result

        return verification

    def get_freshness_threshold(self, category: str) -> int:
        """
        Get freshness threshold for a category.

        Args:
            category: Content category

        Returns:
            Threshold in days
        """
        return self.freshness_thresholds.get(category, 180)

    def set_freshness_threshold(self, category: str, days: int):
        """
        Set freshness threshold for a category.

        Args:
            category: Content category
            days: Threshold in days
        """
        self.freshness_thresholds[category] = days
