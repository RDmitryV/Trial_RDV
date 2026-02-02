"""Tests for autonomous research agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import uuid

from app.services.agent.research_agent import ResearchAgent, AgentState
from app.services.agent.tools import (
    SearchWebTool,
    ParseUrlTool,
    SearchCompaniesTool,
    GetStatisticsTool,
    AnalyzeSentimentTool,
    SaveFindingTool,
)
from app.models.research import Research, ResearchStatus, ResearchType


@pytest.fixture
def mock_research():
    """Create mock research object."""
    return Research(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title="Test Research",
        product_description="Test product for software development",
        industry="IT",
        region="Russia",
        research_type=ResearchType.MARKET,
        status=ResearchStatus.CREATED,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.add = AsyncMock()
    return db


class TestAgentState:
    """Tests for AgentState class."""

    def test_init(self, mock_research):
        """Test state initialization."""
        state = AgentState(mock_research)

        assert state.research == mock_research
        assert state.step_count == 0
        assert state.max_steps == 20
        assert len(state.findings) == 0
        assert len(state.conversation_history) == 0
        assert len(state.visited_urls) == 0
        assert len(state.completed_subtasks) == 0
        assert len(state.pending_subtasks) == 0
        assert state.is_complete is False
        assert state.error is None

    def test_add_message(self, mock_research):
        """Test adding messages to history."""
        state = AgentState(mock_research)

        state.add_message("system", "System message")
        state.add_message("human", "Human message")
        state.add_message("ai", "AI message")

        assert len(state.conversation_history) == 3

    def test_to_dict(self, mock_research):
        """Test state serialization."""
        state = AgentState(mock_research)
        state.step_count = 5
        state.findings.append({"test": "finding"})
        state.visited_urls.add("https://example.com")
        state.completed_subtasks.append("Task 1")

        state_dict = state.to_dict()

        assert state_dict["step_count"] == 5
        assert state_dict["findings_count"] == 1
        assert state_dict["visited_urls_count"] == 1
        assert len(state_dict["completed_subtasks"]) == 1


class TestSearchWebTool:
    """Tests for SearchWebTool."""

    @pytest.mark.asyncio
    async def test_execute_general_search(self):
        """Test general web search."""
        mock_web_search = AsyncMock()
        mock_web_search.search_with_fallback = AsyncMock(return_value=[
            {"title": "Test Result", "url": "https://example.com", "snippet": "Test snippet"}
        ])

        tool = SearchWebTool(mock_web_search)
        result = await tool.execute(query="test query", max_results=10)

        assert result["success"] is True
        assert result["query"] == "test query"
        assert result["results_count"] == 1
        assert len(result["results"]) == 1

    @pytest.mark.asyncio
    async def test_execute_news_search(self):
        """Test news search."""
        mock_web_search = AsyncMock()
        mock_web_search.search_news_duckduckgo = AsyncMock(return_value=[
            {"title": "News", "url": "https://news.com", "snippet": "News snippet"}
        ])

        tool = SearchWebTool(mock_web_search)
        result = await tool.execute(query="test news", search_type="news")

        assert result["success"] is True
        mock_web_search.search_news_duckduckgo.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_error_handling(self):
        """Test error handling in search."""
        mock_web_search = AsyncMock()
        mock_web_search.search_with_fallback = AsyncMock(side_effect=Exception("Search failed"))

        tool = SearchWebTool(mock_web_search)
        result = await tool.execute(query="test")

        assert result["success"] is False
        assert "error" in result

    def test_get_parameters(self):
        """Test parameter schema."""
        mock_web_search = AsyncMock()
        tool = SearchWebTool(mock_web_search)
        params = tool.get_parameters()

        assert params["type"] == "object"
        assert "query" in params["properties"]
        assert "query" in params["required"]


class TestAnalyzeSentimentTool:
    """Tests for AnalyzeSentimentTool."""

    @pytest.mark.asyncio
    async def test_positive_sentiment(self):
        """Test positive sentiment analysis."""
        tool = AnalyzeSentimentTool()
        result = await tool.execute(text="This is great and excellent success with growth")

        assert result["success"] is True
        assert result["sentiment"] == "positive"
        assert result["score"] > 0

    @pytest.mark.asyncio
    async def test_negative_sentiment(self):
        """Test negative sentiment analysis."""
        tool = AnalyzeSentimentTool()
        result = await tool.execute(text="This is bad with failure and decline problems")

        assert result["success"] is True
        assert result["sentiment"] == "negative"
        assert result["score"] < 0

    @pytest.mark.asyncio
    async def test_neutral_sentiment(self):
        """Test neutral sentiment analysis."""
        tool = AnalyzeSentimentTool()
        result = await tool.execute(text="This is a neutral statement about something")

        assert result["success"] is True
        assert result["sentiment"] == "neutral"

    @pytest.mark.asyncio
    async def test_russian_sentiment(self):
        """Test sentiment analysis with Russian text."""
        tool = AnalyzeSentimentTool()
        result = await tool.execute(text="Это хорошо и отлично с успехом и ростом")

        assert result["success"] is True
        assert result["sentiment"] == "positive"


class TestSaveFindingTool:
    """Tests for SaveFindingTool."""

    @pytest.mark.asyncio
    async def test_save_finding(self, mock_db):
        """Test saving a finding."""
        # Mock database responses
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Mock collected data
        mock_collected_data = MagicMock()
        mock_collected_data.id = uuid.uuid4()

        with patch('app.services.agent.tools.DataSource') as mock_source_class, \
             patch('app.services.agent.tools.CollectedData', return_value=mock_collected_data):

            tool = SaveFindingTool(mock_db)
            result = await tool.execute(
                research_id=str(uuid.uuid4()),
                finding_type="competitor",
                title="Test Finding",
                content="Test content",
                source_url="https://example.com",
            )

            assert result["success"] is True
            assert "finding_id" in result
            assert result["finding_type"] == "competitor"
            assert result["title"] == "Test Finding"


class TestResearchAgent:
    """Tests for ResearchAgent."""

    @pytest.mark.asyncio
    async def test_agent_initialization(self, mock_db):
        """Test agent initialization."""
        with patch('app.services.agent.research_agent.settings') as mock_settings:
            mock_settings.default_llm_provider = "openai"
            mock_settings.openai_api_key = "test-key"

            with patch('app.services.agent.research_agent.ChatOpenAI'):
                agent = ResearchAgent(db=mock_db, llm_provider="openai")

                assert agent.db == mock_db
                assert len(agent.tools) == 6
                assert "search_web" in agent.tools
                assert "parse_url" in agent.tools
                assert "search_companies" in agent.tools
                assert "get_statistics" in agent.tools
                assert "analyze_sentiment" in agent.tools
                assert "save_finding" in agent.tools

    @pytest.mark.asyncio
    async def test_agent_create_plan(self, mock_db, mock_research):
        """Test research plan creation."""
        with patch('app.services.agent.research_agent.settings') as mock_settings:
            mock_settings.default_llm_provider = "openai"
            mock_settings.openai_api_key = "test-key"

            with patch('app.services.agent.research_agent.ChatOpenAI') as mock_llm_class:
                # Mock LLM response
                mock_llm = AsyncMock()
                mock_response = MagicMock()
                mock_response.content = '{"subtasks": ["Task 1", "Task 2", "Task 3"]}'
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                mock_llm_class.return_value = mock_llm

                agent = ResearchAgent(db=mock_db)
                state = AgentState(mock_research)

                plan = await agent._create_plan(state)

                assert "subtasks" in plan
                assert len(plan["subtasks"]) > 0

    @pytest.mark.asyncio
    async def test_agent_execute_tool(self, mock_db):
        """Test tool execution."""
        with patch('app.services.agent.research_agent.settings') as mock_settings:
            mock_settings.default_llm_provider = "openai"
            mock_settings.openai_api_key = "test-key"

            with patch('app.services.agent.research_agent.ChatOpenAI'):
                agent = ResearchAgent(db=mock_db)

                # Mock tool
                mock_tool = AsyncMock()
                mock_tool.execute = AsyncMock(return_value={"success": True, "data": "test"})
                agent.tools["test_tool"] = mock_tool

                result = await agent._execute_tool("test_tool", {"arg": "value"})

                assert result["success"] is True
                assert result["tool"] == "test_tool"
                mock_tool.execute.assert_called_once_with(arg="value")

    @pytest.mark.asyncio
    async def test_agent_update_state(self, mock_db, mock_research):
        """Test state update after observation."""
        with patch('app.services.agent.research_agent.settings') as mock_settings:
            mock_settings.default_llm_provider = "openai"
            mock_settings.openai_api_key = "test-key"

            with patch('app.services.agent.research_agent.ChatOpenAI'):
                agent = ResearchAgent(db=mock_db)
                state = AgentState(mock_research)
                state.pending_subtasks = ["Task 1", "Task 2"]

                observation = {
                    "success": True,
                    "result": {"url": "https://example.com"},
                }

                await agent._update_state(state, observation, "parse_url")

                assert "https://example.com" in state.visited_urls
                assert len(state.completed_subtasks) == 1
                assert len(state.pending_subtasks) == 1


@pytest.mark.asyncio
async def test_agent_full_run_mock(mock_db, mock_research):
    """Test full agent run with mocks."""
    with patch('app.services.agent.research_agent.settings') as mock_settings:
        mock_settings.default_llm_provider = "openai"
        mock_settings.openai_api_key = "test-key"

        with patch('app.services.agent.research_agent.ChatOpenAI') as mock_llm_class:
            # Mock LLM to complete immediately
            mock_llm = AsyncMock()

            # Mock plan creation
            plan_response = MagicMock()
            plan_response.content = '{"subtasks": ["Task 1"]}'

            # Mock reasoning to complete
            reasoning_response = MagicMock()
            reasoning_response.content = '{"reasoning": "Done", "action": {"type": "complete"}}'

            # Mock report generation
            report_response = MagicMock()
            report_response.content = "Test Report"

            mock_llm.ainvoke = AsyncMock(side_effect=[plan_response, reasoning_response, report_response])
            mock_llm_class.return_value = mock_llm

            agent = ResearchAgent(db=mock_db)
            result = await agent.run(mock_research)

            assert result["status"] == "completed"
            assert "report" in result
            assert result["steps_taken"] >= 1
