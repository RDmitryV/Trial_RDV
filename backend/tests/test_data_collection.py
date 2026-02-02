"""Tests for data collection services."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.data_collection.web_search_service import WebSearchService
from app.services.data_collection.pipeline_orchestrator import DataCollectionPipeline
from app.models.research import Research, ResearchType
from app.models.data_source import DataSource, SourceType


class TestWebSearchService:
    """Tests for WebSearchService."""

    @pytest.fixture
    def web_search_service(self):
        """Create WebSearchService instance."""
        return WebSearchService()

    @pytest.mark.asyncio
    async def test_search_duckduckgo(self, web_search_service):
        """Test DuckDuckGo search."""
        # Mock AsyncDDGS
        with patch('app.services.data_collection.web_search_service.AsyncDDGS') as mock_ddgs:
            mock_instance = AsyncMock()
            mock_ddgs.return_value.__aenter__.return_value = mock_instance

            # Mock search results
            async def mock_text_search(*args, **kwargs):
                yield {
                    "title": "Test Result",
                    "href": "https://example.com",
                    "body": "Test snippet",
                }

            mock_instance.text = mock_text_search

            results = await web_search_service.search_duckduckgo(
                query="test query",
                max_results=1,
            )

            assert len(results) == 1
            assert results[0]["title"] == "Test Result"
            assert results[0]["url"] == "https://example.com"
            assert results[0]["snippet"] == "Test snippet"
            assert results[0]["source"] == "duckduckgo"

    @pytest.mark.asyncio
    async def test_search_news_duckduckgo(self, web_search_service):
        """Test DuckDuckGo news search."""
        with patch('app.services.data_collection.web_search_service.AsyncDDGS') as mock_ddgs:
            mock_instance = AsyncMock()
            mock_ddgs.return_value.__aenter__.return_value = mock_instance

            async def mock_news_search(*args, **kwargs):
                yield {
                    "title": "News Title",
                    "url": "https://news.example.com",
                    "body": "News snippet",
                    "date": "2024-01-01",
                    "source": "Example News",
                }

            mock_instance.news = mock_news_search

            results = await web_search_service.search_news_duckduckgo(
                query="test news",
                max_results=1,
            )

            assert len(results) == 1
            assert results[0]["title"] == "News Title"
            assert results[0]["url"] == "https://news.example.com"

    @pytest.mark.asyncio
    async def test_search_competitors(self, web_search_service):
        """Test competitor search."""
        with patch.object(
            web_search_service,
            'search_with_fallback',
            new=AsyncMock(return_value=[
                {"title": "Competitor 1", "url": "https://competitor1.com", "snippet": "Test"},
            ])
        ):
            results = await web_search_service.search_competitors(
                industry="IT",
                region="Москва",
                product_keywords=["software", "development"],
                max_results=10,
            )

            assert isinstance(results, list)
            # Should call search_with_fallback multiple times (one for each query)
            assert web_search_service.search_with_fallback.call_count >= 1

    @pytest.mark.asyncio
    async def test_search_industry_news(self, web_search_service):
        """Test industry news search."""
        with patch.object(
            web_search_service,
            'search_news_duckduckgo',
            new=AsyncMock(return_value=[
                {"title": "Industry News", "url": "https://news.com", "snippet": "Test"},
            ])
        ):
            results = await web_search_service.search_industry_news(
                industry="IT",
                region="Москва",
                max_results=10,
            )

            assert isinstance(results, list)
            assert web_search_service.search_news_duckduckgo.call_count >= 1

    @pytest.mark.asyncio
    async def test_comprehensive_search(self, web_search_service):
        """Test comprehensive search."""
        with patch.object(
            web_search_service,
            'search_competitors',
            new=AsyncMock(return_value=[{"title": "Competitor"}])
        ), patch.object(
            web_search_service,
            'search_industry_news',
            new=AsyncMock(return_value=[{"title": "News"}])
        ), patch.object(
            web_search_service,
            'search_market_data',
            new=AsyncMock(return_value=[{"title": "Data"}])
        ):
            results = await web_search_service.comprehensive_search(
                industry="IT",
                region="Москва",
                product_description="software development tools",
                max_results_per_category=5,
            )

            assert "competitors" in results
            assert "news" in results
            assert "market_data" in results
            assert len(results["competitors"]) > 0
            assert len(results["news"]) > 0
            assert len(results["market_data"]) > 0

    def test_convert_to_collected_data(self, web_search_service):
        """Test converting search results to CollectedData."""
        search_results = [
            {
                "title": "Test Result",
                "url": "https://example.com",
                "snippet": "Test snippet",
                "source": "test",
            }
        ]

        collected_data_list = web_search_service.convert_to_collected_data(
            search_results,
            source=None,
            research_id="test-research-id",
        )

        assert len(collected_data_list) == 1
        assert collected_data_list[0].title == "Test Result"
        assert collected_data_list[0].source_url == "https://example.com"
        assert collected_data_list[0].research_id == "test-research-id"


class TestDataCollectionPipeline:
    """Tests for DataCollectionPipeline."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def pipeline(self, mock_db):
        """Create DataCollectionPipeline instance."""
        return DataCollectionPipeline(db=mock_db)

    @pytest.fixture
    def sample_research(self):
        """Create sample research object."""
        return Research(
            id="test-id",
            title="Test Research",
            product_description="Test product",
            industry="IT",
            region="Москва",
            research_type=ResearchType.MARKET,
        )

    @pytest.mark.asyncio
    async def test_get_or_create_source_existing(self, pipeline, mock_db):
        """Test getting existing data source."""
        existing_source = DataSource(
            id="source-id",
            name="Test Source",
            source_type=SourceType.WEB_SCRAPING,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_source
        mock_db.execute.return_value = mock_result

        source = await pipeline._get_or_create_source(
            name="Test Source",
            source_type=SourceType.WEB_SCRAPING,
        )

        assert source.id == "source-id"
        assert source.name == "Test Source"

    @pytest.mark.asyncio
    async def test_get_or_create_source_new(self, pipeline, mock_db):
        """Test creating new data source."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        new_source = DataSource(
            name="New Source",
            source_type=SourceType.API,
        )
        mock_db.refresh.side_effect = lambda x: setattr(x, 'id', 'new-source-id')

        source = await pipeline._get_or_create_source(
            name="New Source",
            source_type=SourceType.API,
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_run_web_search(self, pipeline, sample_research):
        """Test running web search."""
        with patch.object(
            pipeline.web_search,
            'comprehensive_search',
            new=AsyncMock(return_value={
                "competitors": [{"title": "Competitor", "url": "https://comp.com"}],
                "news": [],
                "market_data": [],
            })
        ), patch.object(
            pipeline,
            '_get_or_create_source',
            new=AsyncMock(return_value=DataSource(
                id="source-id",
                name="Test Source",
                source_type=SourceType.WEB_SCRAPING,
            ))
        ):
            results = await pipeline._run_web_search(sample_research)

            assert len(results) > 0
            assert pipeline.db.commit.called

    @pytest.mark.asyncio
    async def test_collect_all_data_partial(self, pipeline, sample_research):
        """Test collecting data with some services disabled."""
        with patch.object(
            pipeline,
            '_run_web_search',
            new=AsyncMock(return_value=[{"title": "Test"}])
        ), patch.object(
            pipeline,
            '_scrape_competitors',
            new=AsyncMock(return_value=[])
        ), patch.object(
            pipeline,
            '_collect_news',
            new=AsyncMock(return_value=[])
        ), patch.object(
            pipeline,
            '_fetch_api_data',
            new=AsyncMock(return_value=[])
        ), patch.object(
            pipeline,
            '_verify_data',
            new=AsyncMock(return_value=[])
        ):
            results = await pipeline.collect_all_data(
                research=sample_research,
                enable_web_search=True,
                enable_scraping=False,
                enable_news=False,
                enable_api_data=False,
                enable_verification=False,
            )

            assert "research_id" in results
            assert "web_search_results" in results
            assert "statistics" in results
            assert results["statistics"]["total_sources"] > 0

    @pytest.mark.asyncio
    async def test_format_data_for_llm(self, pipeline, sample_research, mock_db):
        """Test formatting data for LLM."""
        from app.models.collected_data import CollectedData, DataFormat

        # Mock collected data
        mock_data = [
            CollectedData(
                id="data-1",
                source_id="source-1",
                research_id=sample_research.id,
                title="Test Data",
                processed_content="Test content",
                format=DataFormat.TEXT,
                source_url="https://test.com",
                collected_date=datetime.utcnow(),
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_data
        mock_db.execute.return_value = mock_result

        formatted = await pipeline.format_data_for_llm(sample_research)

        assert isinstance(formatted, str)
        assert "Test Data" in formatted or "Collected Real Data" in formatted
