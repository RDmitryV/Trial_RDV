"""Data collection pipeline orchestrator."""

from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.research import Research
from app.models.data_source import DataSource, SourceType, SourceStatus
from app.models.collected_data import CollectedData
from app.services.data_collection.web_search_service import WebSearchService
from app.services.data_collection.scraper_service import ScraperService
from app.services.data_collection.news_parser import NewsParserService
from app.services.data_collection.api_integrations import APIIntegrationService
from app.services.verification.verification_service import VerificationService


class DataCollectionPipeline:
    """
    Orchestrates the data collection process from multiple sources.

    This pipeline:
    1. Searches web for relevant information
    2. Scrapes competitor websites
    3. Fetches news articles
    4. Calls external APIs for statistics
    5. Verifies collected data
    6. Returns structured, verified data for LLM analysis
    """

    def __init__(
        self,
        db: AsyncSession,
        serpapi_key: Optional[str] = None,
    ):
        """
        Initialize data collection pipeline.

        Args:
            db: Database session
            serpapi_key: Optional SerpAPI key
        """
        self.db = db
        self.web_search = WebSearchService(serpapi_key=serpapi_key)
        self.scraper = ScraperService()
        self.news_parser = NewsParserService()
        self.api_integration = APIIntegrationService()
        self.verification_service = VerificationService(db)

    async def collect_all_data(
        self,
        research: Research,
        enable_web_search: bool = True,
        enable_scraping: bool = True,
        enable_news: bool = True,
        enable_api_data: bool = True,
        enable_verification: bool = True,
    ) -> Dict[str, Any]:
        """
        Run complete data collection pipeline for a research.

        Args:
            research: Research object
            enable_web_search: Whether to enable web search
            enable_scraping: Whether to enable web scraping
            enable_news: Whether to enable news collection
            enable_api_data: Whether to enable API data collection
            enable_verification: Whether to enable data verification

        Returns:
            Dictionary with all collected data and verification results
        """
        print(f"Starting data collection pipeline for research {research.id}")

        results = {
            "research_id": str(research.id),
            "started_at": datetime.utcnow(),
            "web_search_results": [],
            "scraped_data": [],
            "news_articles": [],
            "api_data": [],
            "verified_data": [],
            "statistics": {
                "total_sources": 0,
                "successful_sources": 0,
                "failed_sources": 0,
                "verified_sources": 0,
            },
        }

        # Step 1: Web Search
        if enable_web_search:
            print("Step 1: Running web search...")
            search_results = await self._run_web_search(research)
            results["web_search_results"] = search_results
            results["statistics"]["total_sources"] += len(search_results)

        # Step 2: Scrape Competitor Websites
        if enable_scraping:
            print("Step 2: Scraping competitor websites...")
            scraped_data = await self._scrape_competitors(research, results.get("web_search_results", []))
            results["scraped_data"] = scraped_data
            results["statistics"]["successful_sources"] += len([d for d in scraped_data if d is not None])
            results["statistics"]["failed_sources"] += len([d for d in scraped_data if d is None])

        # Step 3: Collect News
        if enable_news:
            print("Step 3: Collecting news articles...")
            news_articles = await self._collect_news(research)
            results["news_articles"] = news_articles
            results["statistics"]["successful_sources"] += len(news_articles)

        # Step 4: Fetch API Data
        if enable_api_data:
            print("Step 4: Fetching API data...")
            api_data = await self._fetch_api_data(research)
            results["api_data"] = api_data
            results["statistics"]["successful_sources"] += len([d for d in api_data if d is not None])

        # Step 5: Verification
        if enable_verification:
            print("Step 5: Verifying collected data...")
            verified_data = await self._verify_data(research)
            results["verified_data"] = verified_data
            results["statistics"]["verified_sources"] = len(verified_data)

        results["completed_at"] = datetime.utcnow()
        results["duration_seconds"] = (results["completed_at"] - results["started_at"]).total_seconds()

        print(f"Pipeline completed in {results['duration_seconds']:.2f} seconds")
        print(f"Statistics: {results['statistics']}")

        return results

    async def _run_web_search(self, research: Research) -> List[Dict[str, Any]]:
        """
        Run web search for research keywords.

        Args:
            research: Research object

        Returns:
            List of search result dictionaries
        """
        try:
            # Perform comprehensive search
            search_results = await self.web_search.comprehensive_search(
                industry=research.industry,
                region=research.region,
                product_description=research.product_description,
                max_results_per_category=10,
            )

            # Get or create web search data source
            source = await self._get_or_create_source(
                name="Web Search (DuckDuckGo)",
                source_type=SourceType.WEB_SCRAPING,
                url="https://duckduckgo.com",
                category="web_search",
            )

            # Convert to CollectedData and save
            all_results = []
            for category, results in search_results.items():
                for result in results:
                    result["category"] = category
                    all_results.append(result)

            collected_data_list = self.web_search.convert_to_collected_data(
                all_results,
                source=source,
                research_id=str(research.id),
            )

            # Save to database
            for collected_data in collected_data_list:
                self.db.add(collected_data)

            await self.db.commit()

            return all_results

        except Exception as e:
            print(f"Web search error: {e}")
            return []

    async def _scrape_competitors(
        self,
        research: Research,
        search_results: List[Dict[str, Any]],
    ) -> List[Optional[CollectedData]]:
        """
        Scrape competitor websites from search results.

        Args:
            research: Research object
            search_results: List of search results with URLs

        Returns:
            List of CollectedData objects (may contain None for failed scrapes)
        """
        try:
            # Extract competitor URLs from search results
            competitor_urls = []
            for result in search_results:
                if result.get("category") == "competitors" and result.get("url"):
                    competitor_urls.append(result["url"])

            # Limit to prevent too many requests
            competitor_urls = competitor_urls[:15]

            if not competitor_urls:
                return []

            # Get or create scraping source
            source = await self._get_or_create_source(
                name="Competitor Website Scraping",
                source_type=SourceType.WEB_SCRAPING,
                category="competitors",
            )

            # Scrape URLs
            sources_list = [source] * len(competitor_urls)
            collected_data_list = await self.scraper.fetch_multiple_urls(
                urls=competitor_urls,
                sources=sources_list,
            )

            # Link to research and save
            for collected_data in collected_data_list:
                if collected_data:
                    collected_data.research_id = research.id
                    self.db.add(collected_data)

            await self.db.commit()

            return collected_data_list

        except Exception as e:
            print(f"Competitor scraping error: {e}")
            return []

    async def _collect_news(self, research: Research) -> List[Dict[str, Any]]:
        """
        Collect news articles related to research.

        Args:
            research: Research object

        Returns:
            List of news article dictionaries
        """
        try:
            # Search for news
            news_results = await self.web_search.search_industry_news(
                industry=research.industry,
                region=research.region,
                max_results=20,
            )

            if not news_results:
                return []

            # Get or create news source
            source = await self._get_or_create_source(
                name="News Aggregator",
                source_type=SourceType.NEWS,
                category="news",
            )

            # Fetch and parse news articles
            news_urls = [result["url"] for result in news_results if result.get("url")]
            news_urls = news_urls[:10]  # Limit

            parsed_articles = await self.news_parser.fetch_and_parse_multiple(news_urls)

            # Convert to CollectedData
            for article in parsed_articles:
                if article and article.get("content"):
                    collected_data = CollectedData(
                        source_id=source.id,
                        research_id=research.id,
                        title=article.get("title", "No title"),
                        raw_content=str(article),
                        processed_content=article.get("content", ""),
                        format="text",
                        source_url=article.get("url", ""),
                        collected_date=datetime.utcnow(),
                        extra_metadata={
                            "author": article.get("author"),
                            "published_date": article.get("published_date"),
                            "tags": article.get("tags", []),
                            "summary": article.get("summary"),
                        },
                        is_processed="no",
                    )
                    self.db.add(collected_data)

            await self.db.commit()

            return parsed_articles

        except Exception as e:
            print(f"News collection error: {e}")
            return []

    async def _fetch_api_data(self, research: Research) -> List[Optional[CollectedData]]:
        """
        Fetch data from external APIs.

        Args:
            research: Research object

        Returns:
            List of CollectedData objects
        """
        collected_data_list = []

        try:
            # Placeholder API sources (would be configured with real endpoints and keys)
            api_sources = [
                {
                    "name": "Rosstat API",
                    "type": SourceType.GOVERNMENT,
                    "category": "statistics",
                },
                {
                    "name": "HH.ru API (Labor Market)",
                    "type": SourceType.API,
                    "category": "labor_market",
                },
            ]

            for api_config in api_sources:
                source = await self._get_or_create_source(
                    name=api_config["name"],
                    source_type=api_config["type"],
                    category=api_config["category"],
                )

                # Note: These are placeholders - actual API integration requires
                # proper credentials and endpoint configuration
                if "Rosstat" in api_config["name"]:
                    data = await self.api_integration.fetch_rosstat_data(
                        indicator="market_size",
                        region_code=research.region,
                    )
                    if data:
                        collected_data = CollectedData(
                            source_id=source.id,
                            research_id=research.id,
                            title=f"Rosstat data for {research.industry}",
                            raw_content=str(data),
                            processed_content=str(data),
                            format="json",
                            collected_date=datetime.utcnow(),
                            extra_metadata={"api_response": data},
                            is_processed="no",
                        )
                        self.db.add(collected_data)
                        collected_data_list.append(collected_data)

            await self.db.commit()

        except Exception as e:
            print(f"API data fetching error: {e}")

        return collected_data_list

    async def _verify_data(self, research: Research) -> List[Dict[str, Any]]:
        """
        Verify all collected data for research.

        Args:
            research: Research object

        Returns:
            List of verification result dictionaries
        """
        try:
            # Get all collected data for this research
            stmt = select(CollectedData).where(
                CollectedData.research_id == research.id
            )
            result = await self.db.execute(stmt)
            collected_data_list = list(result.scalars().all())

            verification_results = []

            # Verify each collected data item
            for collected_data in collected_data_list[:50]:  # Limit to avoid timeout
                try:
                    verification_result = await self.verification_service.verify_collected_data(
                        collected_data,
                        perform_cross_validation=True,
                        perform_fact_check=True,
                    )
                    verification_results.append(verification_result)
                except Exception as e:
                    print(f"Verification error for data {collected_data.id}: {e}")

            return verification_results

        except Exception as e:
            print(f"Data verification error: {e}")
            return []

    async def _get_or_create_source(
        self,
        name: str,
        source_type: SourceType,
        url: Optional[str] = None,
        category: Optional[str] = None,
    ) -> DataSource:
        """
        Get existing data source or create new one.

        Args:
            name: Source name
            source_type: Source type
            url: Optional URL
            category: Optional category

        Returns:
            DataSource object
        """
        # Try to find existing source
        stmt = select(DataSource).where(DataSource.name == name)
        result = await self.db.execute(stmt)
        source = result.scalar_one_or_none()

        if source:
            return source

        # Create new source
        source = DataSource(
            name=name,
            source_type=source_type,
            url=url,
            category=category,
            status=SourceStatus.ACTIVE,
        )
        self.db.add(source)
        await self.db.commit()
        await self.db.refresh(source)

        return source

    async def get_collected_data_summary(self, research: Research) -> Dict[str, Any]:
        """
        Get summary of collected data for research.

        Args:
            research: Research object

        Returns:
            Summary dictionary
        """
        stmt = select(CollectedData).where(CollectedData.research_id == research.id)
        result = await self.db.execute(stmt)
        collected_data_list = list(result.scalars().all())

        summary = {
            "total_items": len(collected_data_list),
            "by_source": {},
            "by_format": {},
            "total_size_bytes": 0,
            "oldest_date": None,
            "newest_date": None,
        }

        for data in collected_data_list:
            # Count by source
            source_id = str(data.source_id) if data.source_id else "unknown"
            summary["by_source"][source_id] = summary["by_source"].get(source_id, 0) + 1

            # Count by format
            data_format = data.format.value if data.format else "unknown"
            summary["by_format"][data_format] = summary["by_format"].get(data_format, 0) + 1

            # Sum size
            if data.size_bytes:
                summary["total_size_bytes"] += data.size_bytes

            # Track dates
            if data.collected_date:
                if not summary["oldest_date"] or data.collected_date < summary["oldest_date"]:
                    summary["oldest_date"] = data.collected_date
                if not summary["newest_date"] or data.collected_date > summary["newest_date"]:
                    summary["newest_date"] = data.collected_date

        return summary

    async def format_data_for_llm(self, research: Research) -> str:
        """
        Format collected data for LLM analysis.

        Args:
            research: Research object

        Returns:
            Formatted string for LLM prompt
        """
        stmt = select(CollectedData).where(CollectedData.research_id == research.id)
        result = await self.db.execute(stmt)
        collected_data_list = list(result.scalars().all())

        # Build formatted output
        output_parts = ["# Collected Real Data\n"]

        # Group by category
        categories = {}
        for data in collected_data_list:
            category = "Other"
            if data.extra_metadata and isinstance(data.extra_metadata, dict):
                category = data.extra_metadata.get("category", "Other")

            if category not in categories:
                categories[category] = []
            categories[category].append(data)

        # Format each category
        for category, data_list in categories.items():
            output_parts.append(f"\n## {category.capitalize()}\n")

            for i, data in enumerate(data_list[:20], 1):  # Limit per category
                output_parts.append(f"\n### Source {i}: {data.title or 'Untitled'}\n")
                if data.source_url:
                    output_parts.append(f"URL: {data.source_url}\n")

                content = data.processed_content or data.raw_content
                if content:
                    # Truncate long content
                    if len(content) > 1000:
                        content = content[:1000] + "..."
                    output_parts.append(f"\n{content}\n")

        return "\n".join(output_parts)
