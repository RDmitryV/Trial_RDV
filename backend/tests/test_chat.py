"""Tests for chat functionality."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.chat.chat_service import ChatMessage, ChatService
from app.services.chat.websocket_chat_manager import ChatConnectionManager


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def chat_service(mock_db):
    """Create chat service instance."""
    with patch("app.services.chat.chat_service.settings") as mock_settings:
        mock_settings.openai_api_key = "test-key"
        mock_settings.anthropic_api_key = "test-key"

        with patch("app.services.chat.chat_service.ChatOpenAI") as mock_llm:
            mock_llm_instance = MagicMock()
            mock_llm.return_value = mock_llm_instance

            service = ChatService(db=mock_db, llm_provider="openai")
            return service


@pytest.fixture
def chat_manager():
    """Create chat connection manager."""
    return ChatConnectionManager()


class TestChatMessage:
    """Test ChatMessage model."""

    def test_chat_message_creation(self):
        """Test creating a chat message."""
        msg = ChatMessage(role="user", content="Test message")

        assert msg.role == "user"
        assert msg.content == "Test message"
        assert isinstance(msg.timestamp, datetime)

    def test_chat_message_to_dict(self):
        """Test converting message to dictionary."""
        timestamp = datetime.utcnow()
        msg = ChatMessage(role="assistant", content="Response", timestamp=timestamp)

        msg_dict = msg.to_dict()

        assert msg_dict["role"] == "assistant"
        assert msg_dict["content"] == "Response"
        assert msg_dict["timestamp"] == timestamp.isoformat()


class TestChatService:
    """Test ChatService."""

    def test_init_with_openai(self, mock_db):
        """Test initializing with OpenAI provider."""
        with patch("app.services.chat.chat_service.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"

            with patch("app.services.chat.chat_service.ChatOpenAI") as mock_llm:
                service = ChatService(db=mock_db, llm_provider="openai")

                assert service.db == mock_db
                mock_llm.assert_called_once()

    def test_init_with_anthropic(self, mock_db):
        """Test initializing with Anthropic provider."""
        with patch("app.services.chat.chat_service.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"

            with patch("app.services.chat.chat_service.ChatAnthropic") as mock_llm:
                service = ChatService(db=mock_db, llm_provider="anthropic")

                assert service.db == mock_db
                mock_llm.assert_called_once()

    def test_init_with_invalid_provider(self, mock_db):
        """Test initializing with invalid provider."""
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            ChatService(db=mock_db, llm_provider="invalid")

    def test_init_without_api_key(self, mock_db):
        """Test initializing without API key."""
        with patch("app.services.chat.chat_service.settings") as mock_settings:
            mock_settings.openai_api_key = None

            with pytest.raises(ValueError, match="OpenAI API key not configured"):
                ChatService(db=mock_db, llm_provider="openai")

    def test_tools_initialization(self, chat_service):
        """Test that tools are initialized."""
        assert "search_web" in chat_service.tools
        assert "parse_url" in chat_service.tools
        assert "search_companies" in chat_service.tools
        assert "get_statistics" in chat_service.tools
        assert "analyze_sentiment" in chat_service.tools

    @pytest.mark.asyncio
    async def test_chat(self, chat_service):
        """Test basic chat functionality."""
        mock_response = MagicMock()
        mock_response.content = "Test response"
        chat_service.llm.ainvoke = AsyncMock(return_value=mock_response)

        response = await chat_service.chat("Hello")

        assert response == "Test response"
        chat_service.llm.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_research_context(self, chat_service):
        """Test chat with research context."""
        mock_research = MagicMock()
        mock_research.title = "Test Research"
        mock_research.product_description = "Test Product"
        mock_research.industry = "IT"
        mock_research.region = "Moscow"
        mock_research.research_type.value = "market"
        mock_research.status.value = "in_progress"

        mock_response = MagicMock()
        mock_response.content = "Research-aware response"
        chat_service.llm.ainvoke = AsyncMock(return_value=mock_response)

        response = await chat_service.chat(
            "Tell me about the research", research=mock_research
        )

        assert response == "Research-aware response"

    @pytest.mark.asyncio
    async def test_chat_with_history(self, chat_service):
        """Test chat with conversation history."""
        history = [
            ChatMessage(role="user", content="First message"),
            ChatMessage(role="assistant", content="First response"),
        ]

        mock_response = MagicMock()
        mock_response.content = "Contextual response"
        chat_service.llm.ainvoke = AsyncMock(return_value=mock_response)

        response = await chat_service.chat("Follow-up question", history=history)

        assert response == "Contextual response"

    def test_get_system_prompt_without_research(self, chat_service):
        """Test system prompt generation without research."""
        prompt = chat_service._get_system_prompt()

        assert "AI-ассистент" in prompt
        assert "маркетинговых исследований" in prompt

    def test_get_system_prompt_with_research(self, chat_service):
        """Test system prompt generation with research."""
        mock_research = MagicMock()
        mock_research.title = "Test Research"
        mock_research.product_description = "Test Product"
        mock_research.industry = "IT"
        mock_research.region = "Moscow"
        mock_research.research_type.value = "market"
        mock_research.status.value = "in_progress"

        prompt = chat_service._get_system_prompt(research=mock_research)

        assert "Test Research" in prompt
        assert "Test Product" in prompt
        assert "IT" in prompt
        assert "Moscow" in prompt


class TestChatConnectionManager:
    """Test ChatConnectionManager."""

    @pytest.mark.asyncio
    async def test_connect(self, chat_manager):
        """Test connecting a WebSocket."""
        mock_websocket = AsyncMock()
        research_id = "test-research-id"

        await chat_manager.connect(mock_websocket, research_id)

        assert research_id in chat_manager.active_connections
        assert mock_websocket in chat_manager.active_connections[research_id]
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(self, chat_manager):
        """Test disconnecting a WebSocket."""
        mock_websocket = AsyncMock()
        research_id = "test-research-id"

        await chat_manager.connect(mock_websocket, research_id)
        await chat_manager.disconnect(mock_websocket, research_id)

        assert research_id not in chat_manager.active_connections

    @pytest.mark.asyncio
    async def test_send_message(self, chat_manager):
        """Test sending a message."""
        mock_websocket = AsyncMock()
        research_id = "test-research-id"

        await chat_manager.connect(mock_websocket, research_id)
        await chat_manager.send_message(
            research_id, {"type": "test", "content": "Hello"}
        )

        mock_websocket.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_stream_chunk(self, chat_manager):
        """Test streaming a chunk."""
        mock_websocket = AsyncMock()
        research_id = "test-research-id"

        await chat_manager.connect(mock_websocket, research_id)
        await chat_manager.stream_chunk(research_id, "chunk")

        mock_websocket.send_text.assert_called_once()
        call_args = mock_websocket.send_text.call_args[0][0]
        assert "chunk" in call_args
        assert "type" in call_args

    @pytest.mark.asyncio
    async def test_send_error(self, chat_manager):
        """Test sending an error."""
        mock_websocket = AsyncMock()
        research_id = "test-research-id"

        await chat_manager.connect(mock_websocket, research_id)
        await chat_manager.send_error(research_id, "Test error")

        mock_websocket.send_text.assert_called_once()
        call_args = mock_websocket.send_text.call_args[0][0]
        assert "error" in call_args
        assert "Test error" in call_args

    def test_get_connection_count(self, chat_manager):
        """Test getting connection count."""
        assert chat_manager.get_connection_count() == 0

        # Can't easily test with real websockets in unit tests,
        # but we test the method exists and returns an integer
        assert isinstance(chat_manager.get_connection_count(), int)
