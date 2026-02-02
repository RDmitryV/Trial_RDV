"""Fact-checking service for verifying claims and citations."""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
import re
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.collected_data import CollectedData
from app.models.data_source import DataSource
from app.models.source_verification import SourceVerification, TrustedSource


class FactChecker:
    """Service for fact-checking data and verifying claims."""

    def __init__(self, db: AsyncSession):
        """Initialize fact checker."""
        self.db = db
        self.timeout = 10.0

    async def check_facts(
        self,
        collected_data: CollectedData,
        verification: SourceVerification,
    ) -> Dict:
        """
        Perform fact-checking on collected data.

        Args:
            collected_data: Data to fact-check
            verification: Verification record to update

        Returns:
            Dictionary with fact-checking results
        """
        content = collected_data.processed_content or collected_data.raw_content

        # Extract claims from content
        claims = self._extract_claims(content)

        # Verify citations/links
        citations = self._extract_citations(content)
        verified_citations = await self._verify_citations(citations)

        # Check for statistical data
        stats = self._extract_statistics(content)
        # In a real implementation, we would verify these against official sources

        # Calculate fact-check score
        total_claims = len(claims) + len(citations) + len(stats)
        verified_claims = len(verified_citations["valid"])

        fact_check_passed = True
        if total_claims > 0:
            verification_rate = verified_claims / total_claims
            fact_check_passed = verification_rate >= 0.7  # 70% threshold

        # Update verification record
        verification.fact_check_performed = True
        verification.fact_check_passed = fact_check_passed
        verification.verified_claims = verified_claims
        verification.total_claims = total_claims

        result = {
            "fact_check_performed": True,
            "fact_check_passed": fact_check_passed,
            "total_claims": total_claims,
            "verified_claims": verified_claims,
            "verification_rate": verified_claims / total_claims if total_claims > 0 else 0,
            "claims": claims,
            "citations": verified_citations,
            "statistics": stats,
        }

        # Update verification metadata
        if not verification.verification_metadata:
            verification.verification_metadata = {}
        verification.verification_metadata["fact_check"] = result

        return result

    def _extract_claims(self, content: str) -> List[Dict]:
        """
        Extract factual claims from content.

        Args:
            content: Text content

        Returns:
            List of claims with metadata
        """
        if not content:
            return []

        claims = []

        # Look for sentences with specific patterns that indicate claims
        # This is a simplified implementation
        claim_patterns = [
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(процент|%|рубл|долл|евро|тыс|млн|млрд)',
            r'(рост|снижение|увеличение|уменьшение|составил|достиг)\s+(?:на\s+)?(\d+)',
            r'(в\s+\d{4}\s+году)',
        ]

        for pattern in claim_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                claims.append({
                    "type": "numerical_claim",
                    "text": match.group(0),
                    "position": match.start(),
                    "verified": False,
                })

        return claims[:20]  # Limit to 20 claims

    def _extract_citations(self, content: str) -> List[str]:
        """
        Extract URLs and citations from content.

        Args:
            content: Text content

        Returns:
            List of URLs
        """
        if not content:
            return []

        # Extract URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, content)

        return list(set(urls))[:50]  # Limit to 50 unique URLs

    async def _verify_citations(self, citations: List[str]) -> Dict:
        """
        Verify that citations are accessible and valid.

        Args:
            citations: List of URLs to verify

        Returns:
            Dictionary with valid and invalid citations
        """
        valid = []
        invalid = []
        errors = []

        for url in citations[:20]:  # Limit to 20 to avoid long processing
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.head(url, follow_redirects=True)
                    if response.status_code < 400:
                        valid.append({
                            "url": url,
                            "status_code": response.status_code,
                            "accessible": True,
                        })
                    else:
                        invalid.append({
                            "url": url,
                            "status_code": response.status_code,
                            "accessible": False,
                            "error": f"HTTP {response.status_code}",
                        })
            except httpx.RequestError as e:
                invalid.append({
                    "url": url,
                    "accessible": False,
                    "error": str(e)[:100],
                })
            except Exception as e:
                errors.append({
                    "url": url,
                    "error": str(e)[:100],
                })

        return {
            "valid": valid,
            "invalid": invalid,
            "errors": errors,
            "total_checked": len(valid) + len(invalid) + len(errors),
        }

    def _extract_statistics(self, content: str) -> List[Dict]:
        """
        Extract statistical data from content.

        Args:
            content: Text content

        Returns:
            List of statistical data points
        """
        if not content:
            return []

        stats = []

        # Patterns for statistical data
        stat_patterns = [
            # Percentage: "составляет 25%", "рост на 10%"
            (r'(\w+(?:\s+\w+)?)\s+(?:составляет|составил|равен|равна|достиг)\s+(\d+(?:,\d+)?)\s*%', 'percentage'),
            # Money amounts: "10 млн рублей", "5.5 млрд долларов"
            (r'(\d+(?:[,.]\d+)?)\s*(млн|млрд|тыс)\s*(рубл|долл|евро)', 'monetary'),
            # Year-based stats: "в 2024 году составил"
            (r'в\s+(\d{4})\s+году\s+(\w+)\s+составил\s+(\d+(?:[,.]\d+)?)', 'yearly'),
        ]

        for pattern, stat_type in stat_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                stats.append({
                    "type": stat_type,
                    "text": match.group(0),
                    "groups": match.groups(),
                    "verified": False,
                })

        return stats[:30]  # Limit to 30 stats

    async def verify_against_official_sources(
        self,
        claim: str,
        category: str = "general",
    ) -> Dict:
        """
        Verify a claim against official sources.

        Args:
            claim: Claim to verify
            category: Category of claim (e.g., "statistics", "market_data")

        Returns:
            Dictionary with verification result
        """
        # Get trusted sources for the category
        stmt = select(TrustedSource).where(
            TrustedSource.category == category,
            TrustedSource.is_official == True,
        )
        result = await self.db.execute(stmt)
        official_sources = list(result.scalars().all())

        if not official_sources:
            return {
                "verified": False,
                "reason": "No official sources available for verification",
                "sources_checked": 0,
            }

        # In a real implementation, this would:
        # 1. Query official source APIs
        # 2. Search official databases
        # 3. Compare the claim with official data

        return {
            "verified": None,
            "reason": "Official source verification not yet implemented",
            "sources_checked": len(official_sources),
            "available_sources": [s.name for s in official_sources],
        }

    async def flag_unverified_data(
        self,
        verification: SourceVerification,
    ) -> SourceVerification:
        """
        Add flags to verification for unverified data.

        Args:
            verification: Verification record to flag

        Returns:
            Updated verification record
        """
        if not verification.fact_check_performed:
            return verification

        if not verification.fact_check_passed:
            issues = verification.issues_found or []
            if "failed_fact_check" not in issues:
                issues.append("failed_fact_check")
            verification.issues_found = issues

            # Add note
            note = f"Fact-check failed: {verification.verified_claims}/{verification.total_claims} claims verified"
            if verification.verification_notes:
                verification.verification_notes += f"\n{note}"
            else:
                verification.verification_notes = note

        return verification

    def extract_references(self, content: str) -> List[Dict]:
        """
        Extract bibliographic references from content.

        Args:
            content: Text content

        Returns:
            List of references with metadata
        """
        if not content:
            return []

        references = []

        # Common reference patterns (simplified)
        patterns = [
            # Pattern: Author (Year). Title.
            r'([А-ЯA-Z][а-яa-z]+(?:\s+[А-ЯA-Z]\.[А-ЯA-Z]\.)?)\s+\((\d{4})\)\.',
            # Pattern: [1] Reference text
            r'\[(\d+)\]\s+([^\n]+)',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                references.append({
                    "text": match.group(0),
                    "groups": match.groups(),
                    "position": match.start(),
                })

        return references[:50]  # Limit to 50 references

    async def check_citation_quality(
        self,
        collected_data: CollectedData,
    ) -> Dict:
        """
        Check the quality of citations in the data.

        Args:
            collected_data: Data to check

        Returns:
            Dictionary with citation quality metrics
        """
        content = collected_data.processed_content or collected_data.raw_content

        citations = self._extract_citations(content)
        references = self.extract_references(content)

        # Verify citations
        verified_citations = await self._verify_citations(citations)

        total_citations = len(citations) + len(references)
        valid_citations = len(verified_citations["valid"])

        return {
            "total_citations": total_citations,
            "urls_found": len(citations),
            "references_found": len(references),
            "valid_urls": valid_citations,
            "invalid_urls": len(verified_citations["invalid"]),
            "citation_quality_score": valid_citations / len(citations) if citations else 0,
            "has_citations": total_citations > 0,
        }
