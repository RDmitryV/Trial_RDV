"""AI Chat service with agent capabilities."""

import json
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional

from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.research import Research
from app.services.agent.tools import (AnalyzeSentimentTool, GetStatisticsTool,
                                      ParseUrlTool, SearchCompaniesTool,
                                      SearchWebTool)
from app.services.data_collection.api_integrations import APIIntegrationService
from app.services.data_collection.scraper_service import ScraperService
from app.services.data_collection.web_search_service import WebSearchService


class ChatMessage:
    """Chat message model."""

    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None):
        """
        Initialize chat message.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
            timestamp: Message timestamp
        """
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }


class ChatService:
    """
    AI Chat service with agent capabilities.

    Provides interactive chat interface for research assistance with:
    - Natural language interaction
    - Agent tools integration
    - Streaming responses
    - Research context awareness
    """

    def __init__(
        self,
        db: AsyncSession,
        llm_provider: str = "openai",
    ):
        """
        Initialize chat service.

        Args:
            db: Database session
            llm_provider: LLM provider ("openai" or "anthropic")
        """
        self.db = db

        # Initialize LLM
        if llm_provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            self.llm = ChatOpenAI(
                api_key=settings.openai_api_key,
                model="gpt-4",
                temperature=0.7,
                streaming=True,
            )
        elif llm_provider == "anthropic":
            if not settings.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")
            self.llm = ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model="claude-3-opus-20240229",
                temperature=0.7,
                streaming=True,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")

        # Initialize tools
        self.tools: Dict[str, Any] = {}
        self._init_tools()

    def _init_tools(self):
        """Initialize chat agent tools."""
        web_search_service = WebSearchService()
        scraper_service = ScraperService()
        api_integration_service = APIIntegrationService()

        self.tools["search_web"] = SearchWebTool(web_search_service)
        self.tools["parse_url"] = ParseUrlTool(scraper_service, self.db)
        self.tools["search_companies"] = SearchCompaniesTool(web_search_service)
        self.tools["get_statistics"] = GetStatisticsTool(api_integration_service)
        self.tools["analyze_sentiment"] = AnalyzeSentimentTool()

    async def chat_stream(
        self,
        user_message: str,
        research: Optional[Research] = None,
        history: Optional[List[ChatMessage]] = None,
    ) -> AsyncIterator[str]:
        """
        Stream chat response.

        Args:
            user_message: User message
            research: Optional research context
            history: Optional chat history

        Yields:
            Response chunks
        """
        # Build conversation history
        messages = self._build_messages(user_message, research, history)

        # Stream response
        async for chunk in self.llm.astream(messages):
            if hasattr(chunk, "content") and chunk.content:
                yield chunk.content

    async def chat(
        self,
        user_message: str,
        research: Optional[Research] = None,
        history: Optional[List[ChatMessage]] = None,
    ) -> str:
        """
        Get chat response (non-streaming).

        Args:
            user_message: User message
            research: Optional research context
            history: Optional chat history

        Returns:
            Response text
        """
        messages = self._build_messages(user_message, research, history)
        response = await self.llm.ainvoke(messages)
        return response.content

    async def chat_with_tools(
        self,
        user_message: str,
        research: Optional[Research] = None,
        history: Optional[List[ChatMessage]] = None,
    ) -> Dict[str, Any]:
        """
        Chat with agent tools support.

        Args:
            user_message: User message
            research: Optional research context
            history: Optional chat history

        Returns:
            Response with tool usage information
        """
        messages = self._build_messages(user_message, research, history)

        # Add tool availability to system message
        tool_descriptions = []
        for tool_name, tool in self.tools.items():
            tool_descriptions.append(f"- {tool_name}: {tool.description}")

        tools_text = "\n".join(tool_descriptions)
        messages.append(SystemMessage(content=f"""
Доступные инструменты для помощи в исследовании:

{tools_text}

Если нужно использовать инструмент, укажи это в своём ответе в формате:
[TOOL: tool_name {"arg1": "value1", "arg2": "value2"}]
"""))

        response = await self.llm.ainvoke(messages)
        content = response.content

        # Check if tools were requested
        tool_uses = []
        if "[TOOL:" in content:
            # Simple tool extraction (can be improved)
            import re

            tool_pattern = r"\[TOOL:\s*(\w+)\s*({[^}]+})\]"
            matches = re.finditer(tool_pattern, content)

            for match in matches:
                tool_name = match.group(1)
                try:
                    tool_args = json.loads(match.group(2))
                    if tool_name in self.tools:
                        tool_result = await self.tools[tool_name].execute(**tool_args)
                        tool_uses.append(
                            {
                                "tool": tool_name,
                                "arguments": tool_args,
                                "result": tool_result,
                            }
                        )
                except Exception as e:
                    tool_uses.append(
                        {
                            "tool": tool_name,
                            "error": str(e),
                        }
                    )

        return {
            "content": content,
            "tool_uses": tool_uses,
        }

    def _build_messages(
        self,
        user_message: str,
        research: Optional[Research] = None,
        history: Optional[List[ChatMessage]] = None,
    ) -> List[Any]:
        """
        Build message list for LLM.

        Args:
            user_message: User message
            research: Optional research context
            history: Optional chat history

        Returns:
            List of messages
        """
        messages = []

        # System prompt
        system_prompt = self._get_system_prompt(research)
        messages.append(SystemMessage(content=system_prompt))

        # Add history
        if history:
            for msg in history:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    messages.append(AIMessage(content=msg.content))

        # Add current user message
        messages.append(HumanMessage(content=user_message))

        return messages

    def _get_system_prompt(self, research: Optional[Research] = None) -> str:
        """
        Get system prompt for chat.

        Args:
            research: Optional research context

        Returns:
            System prompt
        """
        base_prompt = """Ты - AI-ассистент для маркетинговых исследований в системе "Искусанный Интеллектом Маркетолух".

Твоя задача - помогать пользователям:
1. Отвечать на вопросы по исследованию
2. Уточнять параметры исследования
3. Объяснять собранные данные
4. Предлагать направления анализа
5. Помогать интерпретировать результаты

Будь вежливым, конструктивным и информативным. Отвечай на русском языке.
"""

        if research:
            context = f"""
Контекст текущего исследования:
- Название: {research.title}
- Продукт: {research.product_description}
- Отрасль: {research.industry}
- Регион: {research.region}
- Тип исследования: {research.research_type.value}
- Статус: {research.status.value}
"""
            return base_prompt + context

        return base_prompt
