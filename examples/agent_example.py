"""Example: Using the autonomous research agent."""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

from app.services.agent.research_agent import ResearchAgent
from app.models.research import Research, ResearchType, ResearchStatus
from app.models.user import User
from app.core.database import Base


async def example_agent_research():
    """Example of running autonomous agent research."""

    # Create in-memory SQLite database for example
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=True,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Create test user
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            hashed_password="dummy",
            full_name="Test User",
            is_active=True,
        )
        session.add(user)
        await session.commit()

        # Create research
        research = Research(
            id=uuid.uuid4(),
            user_id=user.id,
            title="Анализ рынка облачных решений в России",
            product_description="Облачная платформа для управления проектами с AI-ассистентом",
            industry="IT / SaaS",
            region="Россия",
            research_type=ResearchType.MARKET,
            status=ResearchStatus.CREATED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(research)
        await session.commit()

        print(f"\\n{'='*60}")
        print(f"Research created: {research.id}")
        print(f"Title: {research.title}")
        print(f"{'='*60}\\n")

        # Create progress callback
        async def progress_callback(data: dict):
            """Print progress updates."""
            timestamp = data.get('timestamp', '')
            message = data.get('message', '')
            state = data.get('state', {})

            print(f"\\n[{timestamp}]")
            print(f"  Message: {message}")
            print(f"  Step: {state.get('step_count', 0)}/{state.get('max_steps', 0)}")
            print(f"  Findings: {state.get('findings_count', 0)}")
            print(f"  Completed subtasks: {len(state.get('completed_subtasks', []))}")
            print(f"  Pending subtasks: {len(state.get('pending_subtasks', []))}")

        # Create agent
        print("\\nInitializing agent...")
        agent = ResearchAgent(
            db=session,
            llm_provider="openai",  # Change to "anthropic" if using Claude
            progress_callback=progress_callback,
        )

        print("Starting autonomous research...\\n")

        # Run agent (NOTE: This requires valid API keys)
        try:
            results = await agent.run(research)

            print(f"\\n{'='*60}")
            print("RESEARCH COMPLETED")
            print(f"{'='*60}")
            print(f"\\nStatus: {results['status']}")
            print(f"Steps taken: {results['steps_taken']}")
            print(f"Findings collected: {results['findings_count']}")
            print(f"\\nReport Preview:")
            print(f"{'-'*60}")
            print(results['report'][:500] + "..." if len(results['report']) > 500 else results['report'])
            print(f"{'-'*60}")

        except ValueError as e:
            print(f"\\nError: {e}")
            print("\\nPlease set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.")
            print("Example: export OPENAI_API_KEY='your-key-here'")

        except Exception as e:
            print(f"\\nUnexpected error: {e}")
            import traceback
            traceback.print_exc()


async def example_tools():
    """Example of using individual agent tools."""
    from app.services.agent.tools import (
        SearchWebTool,
        AnalyzeSentimentTool,
    )
    from app.services.data_collection.web_search_service import WebSearchService

    print("\\n" + "="*60)
    print("TESTING INDIVIDUAL TOOLS")
    print("="*60 + "\\n")

    # Test SearchWebTool
    print("1. Testing SearchWebTool...")
    web_search_service = WebSearchService()
    search_tool = SearchWebTool(web_search_service)

    result = await search_tool.execute(
        query="облачные решения россия 2024",
        max_results=5
    )

    print(f"   Success: {result['success']}")
    print(f"   Results found: {result.get('results_count', 0)}")
    if result.get('results'):
        print(f"   First result: {result['results'][0].get('title', 'N/A')}")

    # Test AnalyzeSentimentTool
    print("\\n2. Testing AnalyzeSentimentTool...")
    sentiment_tool = AnalyzeSentimentTool()

    positive_text = "Отличный продукт с хорошими возможностями и успешным ростом"
    result = await sentiment_tool.execute(text=positive_text)

    print(f"   Success: {result['success']}")
    print(f"   Text: '{positive_text}'")
    print(f"   Sentiment: {result.get('sentiment', 'N/A')}")
    print(f"   Score: {result.get('score', 0):.2f}")

    negative_text = "Плохой продукт с проблемами и падением качества"
    result = await sentiment_tool.execute(text=negative_text)

    print(f"\\n   Text: '{negative_text}'")
    print(f"   Sentiment: {result.get('sentiment', 'N/A')}")
    print(f"   Score: {result.get('score', 0):.2f}")

    print("\\n" + "="*60 + "\\n")


async def main():
    """Run examples."""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║        Autonomous Research Agent - Examples              ║
    ║                                                          ║
    ║  This example demonstrates:                              ║
    ║  1. Running autonomous agent research                    ║
    ║  2. Using individual agent tools                         ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    # Run tool examples (don't require API keys)
    await example_tools()

    # Run full agent example (requires API keys)
    print("\\nDo you want to run the full agent example?")
    print("(This requires OPENAI_API_KEY or ANTHROPIC_API_KEY)")
    print("Type 'yes' to continue, or press Enter to skip: ", end='')

    try:
        response = input().strip().lower()
        if response == 'yes':
            await example_agent_research()
        else:
            print("\\nSkipping full agent example.")
    except (EOFError, KeyboardInterrupt):
        print("\\nSkipping full agent example.")

    print("\\nExamples completed!")


if __name__ == "__main__":
    asyncio.run(main())
