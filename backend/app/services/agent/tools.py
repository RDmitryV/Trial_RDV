"""Agent tools for autonomous research."""

from typing import Any, Dict, Optional
from abc import ABC, abstractmethod
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.data_collection.web_search_service import WebSearchService
from app.services.data_collection.scraper_service import ScraperService
from app.services.data_collection.api_integrations import APIIntegrationService
from app.models.collected_data import CollectedData, DataFormat
from app.models.data_source import DataSource, SourceType


class BaseTool(ABC):
    """Base class for agent tools."""

    def __init__(self, name: str, description: str):
        """
        Initialize tool.

        Args:
            name: Tool name
            description: Tool description
        """
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool.

        Returns:
            Dictionary with tool execution results
        """
        pass

    def get_schema(self) -> Dict[str, Any]:
        """
        Get tool schema for LLM function calling.

        Returns:
            Tool schema dictionary
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.get_parameters(),
        }

    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """
        Get tool parameters schema.

        Returns:
            Parameters schema dictionary
        """
        pass


class SearchWebTool(BaseTool):
    """Tool for searching the web."""

    def __init__(self, web_search_service: WebSearchService):
        """
        Initialize search web tool.

        Args:
            web_search_service: Web search service instance
        """
        super().__init__(
            name="search_web",
            description="Search the web for information about markets, competitors, or industry trends. Use this to find relevant websites, articles, and data sources.",
        )
        self.web_search = web_search_service

    async def execute(self, query: str, max_results: int = 10, search_type: str = "general") -> Dict[str, Any]:
        """
        Execute web search.

        Args:
            query: Search query
            max_results: Maximum number of results
            search_type: Type of search ("general", "news", "market_data")

        Returns:
            Search results
        """
        try:
            if search_type == "news":
                results = await self.web_search.search_news_duckduckgo(query, max_results)
            else:
                results = await self.web_search.search_with_fallback(query, max_results)

            return {
                "success": True,
                "query": query,
                "results_count": len(results),
                "results": results,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
            }

    def get_parameters(self) -> Dict[str, Any]:
        """Get tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 10)",
                    "default": 10,
                },
                "search_type": {
                    "type": "string",
                    "enum": ["general", "news", "market_data"],
                    "description": "Type of search to perform",
                    "default": "general",
                },
            },
            "required": ["query"],
        }


class ParseUrlTool(BaseTool):
    """Tool for parsing and extracting content from URLs."""

    def __init__(self, scraper_service: ScraperService, db: AsyncSession):
        """
        Initialize parse URL tool.

        Args:
            scraper_service: Scraper service instance
            db: Database session
        """
        super().__init__(
            name="parse_url",
            description="Parse and extract content from a specific URL. Use this to get detailed information from websites found during web searches.",
        )
        self.scraper = scraper_service
        self.db = db

    async def execute(self, url: str, source_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute URL parsing.

        Args:
            url: URL to parse
            source_id: Optional source ID

        Returns:
            Parsed content
        """
        try:
            # Create a temporary source if not provided
            if not source_id:
                from sqlalchemy import select
                stmt = select(DataSource).where(DataSource.name == "Agent Web Scraping")
                result = await self.db.execute(stmt)
                source = result.scalar_one_or_none()

                if not source:
                    source = DataSource(
                        name="Agent Web Scraping",
                        source_type=SourceType.WEB_SCRAPING,
                        category="agent_tools",
                    )
                    self.db.add(source)
                    await self.db.commit()
                    await self.db.refresh(source)

                source_id = str(source.id)

            # Fetch URL
            collected_data = await self.scraper.fetch_url(url, source_id)

            if collected_data:
                return {
                    "success": True,
                    "url": url,
                    "title": collected_data.title,
                    "content": collected_data.processed_content[:2000],  # Truncate for agent context
                    "full_content_length": len(collected_data.processed_content or ""),
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to fetch URL",
                    "url": url,
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "url": url,
            }

    def get_parameters(self) -> Dict[str, Any]:
        """Get tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to parse and extract content from",
                },
            },
            "required": ["url"],
        }


class SearchCompaniesTool(BaseTool):
    """Tool for searching companies in a specific industry and region."""

    def __init__(self, web_search_service: WebSearchService):
        """
        Initialize search companies tool.

        Args:
            web_search_service: Web search service instance
        """
        super().__init__(
            name="search_companies",
            description="Search for companies in a specific industry and region. Use this to find competitors and market players.",
        )
        self.web_search = web_search_service

    async def execute(self, industry: str, region: str, max_results: int = 15) -> Dict[str, Any]:
        """
        Execute company search.

        Args:
            industry: Industry/sector
            region: Region/location
            max_results: Maximum number of results

        Returns:
            Company search results
        """
        try:
            # Extract basic keywords for search
            keywords = industry.split()[:3]

            results = await self.web_search.search_competitors(
                industry=industry,
                region=region,
                product_keywords=keywords,
                max_results=max_results,
            )

            return {
                "success": True,
                "industry": industry,
                "region": region,
                "companies_found": len(results),
                "results": results,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "industry": industry,
                "region": region,
            }

    def get_parameters(self) -> Dict[str, Any]:
        """Get tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "industry": {
                    "type": "string",
                    "description": "The industry or sector to search in",
                },
                "region": {
                    "type": "string",
                    "description": "The region or location to search in",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 15)",
                    "default": 15,
                },
            },
            "required": ["industry", "region"],
        }


class GetStatisticsTool(BaseTool):
    """Tool for getting statistics and market data."""

    def __init__(self, api_integration_service: APIIntegrationService):
        """
        Initialize get statistics tool.

        Args:
            api_integration_service: API integration service instance
        """
        super().__init__(
            name="get_statistics",
            description="Get statistical data and market metrics for a specific region. Use this to find market size, growth rates, and other quantitative data.",
        )
        self.api_integration = api_integration_service

    async def execute(self, metric: str, region: str) -> Dict[str, Any]:
        """
        Execute statistics retrieval.

        Args:
            metric: Metric to retrieve (e.g., "market_size", "growth_rate")
            region: Region code

        Returns:
            Statistics data
        """
        try:
            # Try to fetch from available APIs
            data = None

            # Try Rosstat for Russian regions
            if region.lower() in ["россия", "russia", "ru"]:
                data = await self.api_integration.fetch_rosstat_data(
                    indicator=metric,
                    region_code=region,
                )

            if data:
                return {
                    "success": True,
                    "metric": metric,
                    "region": region,
                    "data": data,
                }
            else:
                return {
                    "success": False,
                    "message": "No data available for this metric and region. Consider using web search instead.",
                    "metric": metric,
                    "region": region,
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "metric": metric,
                "region": region,
            }

    def get_parameters(self) -> Dict[str, Any]:
        """Get tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "description": "The metric or indicator to retrieve (e.g., 'market_size', 'growth_rate', 'employment')",
                },
                "region": {
                    "type": "string",
                    "description": "The region code or name",
                },
            },
            "required": ["metric", "region"],
        }


class AnalyzeSentimentTool(BaseTool):
    """Tool for analyzing sentiment of text content."""

    def __init__(self):
        """Initialize analyze sentiment tool."""
        super().__init__(
            name="analyze_sentiment",
            description="Analyze the sentiment and tone of text content. Use this to understand public opinion, review sentiment, or market mood.",
        )

    async def execute(self, text: str) -> Dict[str, Any]:
        """
        Execute sentiment analysis.

        Args:
            text: Text to analyze

        Returns:
            Sentiment analysis results
        """
        try:
            # Simple sentiment analysis based on positive/negative keywords
            # In production, this could use a proper NLP model
            positive_keywords = [
                "хорошо", "отлично", "успех", "рост", "положительный", "увеличение",
                "good", "great", "success", "growth", "positive", "increase"
            ]
            negative_keywords = [
                "плохо", "провал", "падение", "отрицательный", "снижение", "проблема",
                "bad", "failure", "decline", "negative", "decrease", "problem"
            ]

            text_lower = text.lower()
            positive_count = sum(1 for word in positive_keywords if word in text_lower)
            negative_count = sum(1 for word in negative_keywords if word in text_lower)

            total = positive_count + negative_count
            if total == 0:
                sentiment = "neutral"
                score = 0.0
            else:
                score = (positive_count - negative_count) / total
                if score > 0.2:
                    sentiment = "positive"
                elif score < -0.2:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"

            return {
                "success": True,
                "sentiment": sentiment,
                "score": score,
                "positive_indicators": positive_count,
                "negative_indicators": negative_count,
                "text_length": len(text),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def get_parameters(self) -> Dict[str, Any]:
        """Get tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text content to analyze for sentiment",
                },
            },
            "required": ["text"],
        }


class SaveFindingTool(BaseTool):
    """Tool for saving important findings during research."""

    def __init__(self, db: AsyncSession):
        """
        Initialize save finding tool.

        Args:
            db: Database session
        """
        super().__init__(
            name="save_finding",
            description="Save an important finding or insight discovered during research. Use this to store key information for the final report.",
        )
        self.db = db

    async def execute(
        self,
        research_id: str,
        finding_type: str,
        title: str,
        content: str,
        source_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute finding save.

        Args:
            research_id: Research ID
            finding_type: Type of finding (e.g., "competitor", "trend", "statistic")
            title: Finding title
            content: Finding content
            source_url: Optional source URL
            metadata: Optional metadata

        Returns:
            Save result
        """
        try:
            from sqlalchemy import select

            # Get or create a data source for agent findings
            stmt = select(DataSource).where(DataSource.name == "Agent Findings")
            result = await self.db.execute(stmt)
            source = result.scalar_one_or_none()

            if not source:
                source = DataSource(
                    name="Agent Findings",
                    source_type=SourceType.API,
                    category="agent_findings",
                )
                self.db.add(source)
                await self.db.commit()
                await self.db.refresh(source)

            # Create collected data entry
            collected_data = CollectedData(
                source_id=source.id,
                research_id=research_id,
                title=title,
                raw_content=content,
                processed_content=content,
                format=DataFormat.TEXT,
                source_url=source_url,
                collected_date=datetime.utcnow(),
                size_bytes=len(content.encode("utf-8")),
                extra_metadata={
                    "finding_type": finding_type,
                    "agent_generated": True,
                    **(metadata or {}),
                },
                is_processed="no",
            )

            self.db.add(collected_data)
            await self.db.commit()
            await self.db.refresh(collected_data)

            return {
                "success": True,
                "finding_id": str(collected_data.id),
                "finding_type": finding_type,
                "title": title,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def get_parameters(self) -> Dict[str, Any]:
        """Get tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "research_id": {
                    "type": "string",
                    "description": "The research ID to associate this finding with",
                },
                "finding_type": {
                    "type": "string",
                    "description": "Type of finding (e.g., 'competitor', 'trend', 'statistic', 'insight')",
                },
                "title": {
                    "type": "string",
                    "description": "Brief title for the finding",
                },
                "content": {
                    "type": "string",
                    "description": "Detailed content of the finding",
                },
                "source_url": {
                    "type": "string",
                    "description": "Optional URL of the source",
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional additional metadata",
                },
            },
            "required": ["research_id", "finding_type", "title", "content"],
        }
