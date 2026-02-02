"""Autonomous research agent using ReAct pattern."""

import json
import asyncio
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, AIMessage, SystemMessage

from app.models.research import Research, ResearchStatus
from app.services.agent.tools import (
    BaseTool,
    SearchWebTool,
    ParseUrlTool,
    SearchCompaniesTool,
    GetStatisticsTool,
    AnalyzeSentimentTool,
    SaveFindingTool,
)
from app.services.data_collection.web_search_service import WebSearchService
from app.services.data_collection.scraper_service import ScraperService
from app.services.data_collection.api_integrations import APIIntegrationService
from app.core.config import settings


class AgentState:
    """Agent state management."""

    def __init__(self, research: Research):
        """
        Initialize agent state.

        Args:
            research: Research object
        """
        self.research = research
        self.step_count = 0
        self.max_steps = 20
        self.findings: List[Dict[str, Any]] = []
        self.conversation_history: List[Any] = []
        self.visited_urls: set = set()
        self.completed_subtasks: List[str] = []
        self.pending_subtasks: List[str] = []
        self.is_complete = False
        self.error: Optional[str] = None

    def add_message(self, role: str, content: str):
        """Add message to conversation history."""
        if role == "system":
            self.conversation_history.append(SystemMessage(content=content))
        elif role == "human":
            self.conversation_history.append(HumanMessage(content=content))
        elif role == "ai":
            self.conversation_history.append(AIMessage(content=content))

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "research_id": str(self.research.id),
            "step_count": self.step_count,
            "max_steps": self.max_steps,
            "findings_count": len(self.findings),
            "visited_urls_count": len(self.visited_urls),
            "completed_subtasks": self.completed_subtasks,
            "pending_subtasks": self.pending_subtasks,
            "is_complete": self.is_complete,
            "error": self.error,
        }


class ResearchAgent:
    """
    Autonomous research agent using ReAct pattern.

    This agent conducts market research by:
    1. Reasoning about the current state
    2. Selecting and executing actions (tools)
    3. Observing results
    4. Repeating until research is complete
    """

    def __init__(
        self,
        db: AsyncSession,
        llm_provider: str = "openai",
        progress_callback: Optional[Callable] = None,
    ):
        """
        Initialize research agent.

        Args:
            db: Database session
            llm_provider: LLM provider ("openai" or "anthropic")
            progress_callback: Optional callback for progress updates
        """
        self.db = db
        self.progress_callback = progress_callback

        # Initialize LLM
        if llm_provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            self.llm = ChatOpenAI(
                api_key=settings.openai_api_key,
                model="gpt-4",
                temperature=0.7,
            )
        elif llm_provider == "anthropic":
            if not settings.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")
            self.llm = ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model="claude-3-opus-20240229",
                temperature=0.7,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")

        # Initialize tools
        self.tools: Dict[str, BaseTool] = {}
        self._init_tools()

    def _init_tools(self):
        """Initialize agent tools."""
        web_search_service = WebSearchService()
        scraper_service = ScraperService()
        api_integration_service = APIIntegrationService()

        self.tools["search_web"] = SearchWebTool(web_search_service)
        self.tools["parse_url"] = ParseUrlTool(scraper_service, self.db)
        self.tools["search_companies"] = SearchCompaniesTool(web_search_service)
        self.tools["get_statistics"] = GetStatisticsTool(api_integration_service)
        self.tools["analyze_sentiment"] = AnalyzeSentimentTool()
        self.tools["save_finding"] = SaveFindingTool(self.db)

    async def run(self, research: Research) -> Dict[str, Any]:
        """
        Run autonomous research.

        Args:
            research: Research object

        Returns:
            Research results
        """
        # Initialize state
        state = AgentState(research)

        # Update research status
        research.status = ResearchStatus.COLLECTING_DATA
        await self.db.commit()

        # Create initial plan
        await self._notify_progress("Creating research plan...", state)
        plan = await self._create_plan(state)
        state.pending_subtasks = plan.get("subtasks", [])

        # Add system prompt
        state.add_message("system", self._get_system_prompt())

        # ReAct loop
        while not state.is_complete and state.step_count < state.max_steps:
            state.step_count += 1

            await self._notify_progress(
                f"Step {state.step_count}/{state.max_steps}: Reasoning...",
                state
            )

            # Reasoning: Analyze current state
            thought = await self._reason(state)

            reasoning = thought.get('reasoning', 'Planning action...')
            await self._notify_progress(
                f"Step {state.step_count}: {reasoning}",
                state
            )

            # Action: Select and execute action
            action_decision = thought.get("action", {})

            if action_decision.get("type") == "complete":
                state.is_complete = True
                await self._notify_progress("Research completed!", state)
                break

            if action_decision.get("type") == "tool_call":
                tool_name = action_decision.get("tool")
                tool_args = action_decision.get("arguments", {})

                if tool_name in self.tools:
                    await self._notify_progress(
                        f"Step {state.step_count}: Executing {tool_name}...",
                        state
                    )

                    # Execute tool
                    observation = await self._execute_tool(tool_name, tool_args)

                    # Update state based on observation
                    await self._update_state(state, observation, tool_name)

                    await self._notify_progress(
                        f"Step {state.step_count}: Action completed",
                        state
                    )
                else:
                    state.error = f"Unknown tool: {tool_name}"
                    break

            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)

        # Update research status
        if state.is_complete:
            research.status = ResearchStatus.ANALYZING
        elif state.error:
            research.status = ResearchStatus.FAILED
        await self.db.commit()

        # Generate final report
        report = await self._generate_report(state)

        return {
            "status": "completed" if state.is_complete else "failed",
            "steps_taken": state.step_count,
            "findings_count": len(state.findings),
            "report": report,
            "state": state.to_dict(),
        }

    async def _create_plan(self, state: AgentState) -> Dict[str, Any]:
        """
        Create initial research plan.

        Args:
            state: Agent state

        Returns:
            Research plan
        """
        research = state.research

        prompt = f"""Create a research plan for the following market research:

Product: {research.product_description}
Industry: {research.industry}
Region: {research.region}
Research Type: {research.research_type.value}

Break down the research into 5-8 specific subtasks that should be completed.
Each subtask should be actionable and focused.

Return a JSON object with the following structure:
{{
  "subtasks": [
    "Subtask 1 description",
    "Subtask 2 description",
    ...
  ]
}}
"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])

        try:
            # Try to parse JSON from response
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            plan = json.loads(content.strip())
            return plan
        except Exception:
            # Fallback plan
            industry = research.industry
            region = research.region
            return {
                "subtasks": [
                    f"Search for market information about {industry} in "
                    f"{region}",
                    f"Find competitors in {industry}",
                    f"Search for recent news and trends in {industry}",
                    "Collect statistical data about market size and growth",
                    "Analyze sentiment of market information",
                ]
            }

    async def _reason(self, state: AgentState) -> Dict[str, Any]:
        """
        Reason about current state and decide next action.

        Args:
            state: Agent state

        Returns:
            Thought with reasoning and action decision
        """
        research = state.research

        # Build context
        context_parts = [
            "Research Goal:",
            f"- Product: {research.product_description}",
            f"- Industry: {research.industry}",
            f"- Region: {research.region}",
            f"- Type: {research.research_type.value}",
            "",
            "Progress:",
            f"- Step: {state.step_count}/{state.max_steps}",
            f"- Findings collected: {len(state.findings)}",
            f"- URLs visited: {len(state.visited_urls)}",
            "",
            "Completed subtasks:",
        ]

        for task in state.completed_subtasks:
            context_parts.append(f"  ✓ {task}")

        context_parts.append("")
        context_parts.append("Pending subtasks:")

        for task in state.pending_subtasks:
            context_parts.append(f"  - {task}")

        context_parts.extend([
            "",
            "Available tools:",
        ])

        for tool_name, tool in self.tools.items():
            context_parts.append(f"  - {tool_name}: {tool.description}")

        context_parts.extend([
            "",
            "Based on the current state, decide the next action.",
            "",
            "Return a JSON object with:",
            '{',
            '  "reasoning": "Your reasoning about what to do next",',
            '  "action": {',
            '    "type": "tool_call" or "complete",',
            '    "tool": "tool_name" (if tool_call),',
            '    "arguments": {...} (if tool_call)',
            '  }',
            '}',
            "",
            "Choose to complete when you have gathered sufficient information.",
        ])

        prompt = "\n".join(context_parts)

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=self._get_system_prompt()),
                HumanMessage(content=prompt),
            ])

            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            thought = json.loads(content.strip())
            return thought
        except Exception as e:
            # Fallback: search web for industry
            return {
                "reasoning": f"Error in reasoning: {str(e)}. Falling back to web search.",
                "action": {
                    "type": "tool_call",
                    "tool": "search_web",
                    "arguments": {
                        "query": f"{research.industry} {research.region} market",
                        "max_results": 10,
                    }
                }
            }

    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool.

        Args:
            tool_name: Tool name
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        tool = self.tools[tool_name]
        try:
            result = await tool.execute(**arguments)
            return {
                "tool": tool_name,
                "success": True,
                "result": result,
            }
        except Exception as e:
            return {
                "tool": tool_name,
                "success": False,
                "error": str(e),
            }

    async def _update_state(
        self,
        state: AgentState,
        observation: Dict[str, Any],
        tool_name: str,
    ):
        """
        Update state based on observation.

        Args:
            state: Agent state
            observation: Observation from tool execution
            tool_name: Tool that was executed
        """
        if not observation.get("success"):
            return

        result = observation.get("result", {})

        # Track visited URLs
        if tool_name == "parse_url":
            url = result.get("url")
            if url:
                state.visited_urls.add(url)

        # Track findings
        if tool_name == "save_finding":
            state.findings.append(result)

        # Mark subtask as completed if relevant
        if state.pending_subtasks:
            # Simple heuristic: mark first pending subtask as completed
            completed_task = state.pending_subtasks.pop(0)
            state.completed_subtasks.append(completed_task)

    async def _generate_report(self, state: AgentState) -> str:
        """
        Generate final research report.

        Args:
            state: Agent state

        Returns:
            Report text
        """
        research = state.research

        prompt = f"""Generate a comprehensive market research report based on the following:

Research Details:
- Product: {research.product_description}
- Industry: {research.industry}
- Region: {research.region}
- Type: {research.research_type.value}

Research Statistics:
- Steps taken: {state.step_count}
- Findings collected: {len(state.findings)}
- URLs visited: {len(state.visited_urls)}

Findings:
{json.dumps(state.findings, indent=2, ensure_ascii=False)}

Create a professional market research report in Russian that includes:
1. Executive Summary
2. Market Overview
3. Competitive Analysis
4. Key Findings
5. Recommendations

The report should be well-structured and based on the collected findings.
"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content

    def _get_system_prompt(self) -> str:
        """Get system prompt for agent."""
        return """Ты - автономный AI-агент для проведения маркетинговых исследований.

Твоя задача - самостоятельно собирать и анализировать информацию о рынке, конкурентах, трендах.

Принципы работы:
1. Анализируй текущее состояние исследования
2. Принимай решения о следующих шагах
3. Используй доступные инструменты для сбора данных
4. Сохраняй важные находки
5. Адаптируй план по мере получения новой информации

Будь методичным и тщательным. Собирай достаточно данных для качественного анализа.
"""

    async def _notify_progress(self, message: str, state: AgentState):
        """
        Notify about progress.

        Args:
            message: Progress message
            state: Current state
        """
        if self.progress_callback:
            await self.progress_callback({
                "timestamp": datetime.utcnow().isoformat(),
                "message": message,
                "state": state.to_dict(),
            })
