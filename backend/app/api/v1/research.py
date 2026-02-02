"""Research endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.research import Research, ResearchStatus, ResearchType
from app.services.llm_service import LLMService
from app.services.data_collection.pipeline_orchestrator import DataCollectionPipeline
from app.services.agent.research_agent import ResearchAgent
from app.services.agent.websocket_manager import manager as ws_manager
from app.core.config import settings

router = APIRouter()


class ResearchCreate(BaseModel):
    """Research creation schema."""
    title: str
    product_description: str
    industry: str
    region: str
    research_type: ResearchType = ResearchType.MARKET
    additional_params: dict | None = None


class ResearchResponse(BaseModel):
    """Research response schema."""
    id: str
    title: str
    product_description: str
    industry: str
    region: str
    research_type: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResearchAnalysisResponse(BaseModel):
    """Research analysis response."""
    research_id: str
    analysis: str
    status: str


@router.post("/", response_model=ResearchResponse, status_code=status.HTTP_201_CREATED)
async def create_research(
    research_data: ResearchCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new research."""
    research = Research(
        user_id=current_user.id,
        title=research_data.title,
        product_description=research_data.product_description,
        industry=research_data.industry,
        region=research_data.region,
        research_type=research_data.research_type,
        additional_params=research_data.additional_params,
    )

    db.add(research)
    await db.commit()
    await db.refresh(research)

    return research


@router.get("/", response_model=list[ResearchResponse])
async def list_researches(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 20,
):
    """List user's researches."""
    result = await db.execute(
        select(Research)
        .where(Research.user_id == current_user.id)
        .order_by(Research.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    researches = result.scalars().all()
    return researches


@router.get("/{research_id}", response_model=ResearchResponse)
async def get_research(
    research_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific research."""
    result = await db.execute(
        select(Research).where(Research.id == research_id, Research.user_id == current_user.id)
    )
    research = result.scalar_one_or_none()

    if not research:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research not found",
        )

    return research


@router.post("/{research_id}/analyze", response_model=ResearchAnalysisResponse)
async def analyze_research(
    research_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    llm_service: Annotated[LLMService, Depends(LLMService)],
):
    """Analyze research using LLM with real data collection."""
    # Get research
    result = await db.execute(
        select(Research).where(Research.id == research_id, Research.user_id == current_user.id)
    )
    research = result.scalar_one_or_none()

    if not research:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research not found",
        )

    # Update status to analyzing
    research.status = ResearchStatus.ANALYZING
    await db.commit()

    try:
        # Step 1: Collect real data from multiple sources
        pipeline = DataCollectionPipeline(
            db=db,
            serpapi_key=getattr(settings, 'serpapi_key', None),
        )

        # Run data collection pipeline
        await pipeline.collect_all_data(
            research=research,
            enable_web_search=True,
            enable_scraping=True,
            enable_news=True,
            enable_api_data=True,
            enable_verification=True,
        )

        # Step 2: Format collected data for LLM
        collected_data_text = await pipeline.format_data_for_llm(research)

        # Step 3: Perform analysis using LLM with real data
        analysis_result = await llm_service.analyze_market_with_data(
            product_description=research.product_description,
            industry=research.industry,
            region=research.region,
            collected_data=collected_data_text,
        )

        # Update status to completed
        research.status = ResearchStatus.COMPLETED
        research.completed_at = datetime.utcnow()
        await db.commit()

        return ResearchAnalysisResponse(
            research_id=str(research.id),
            analysis=analysis_result,
            status=research.status.value,
        )

    except Exception as e:
        # Update status to failed
        research.status = ResearchStatus.FAILED
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )


async def _run_agent_research(research_id: str, db: AsyncSession):
    """
    Background task to run agent research.

    Args:
        research_id: Research ID
        db: Database session
    """
    # Get research
    result = await db.execute(
        select(Research).where(Research.id == research_id)
    )
    research = result.scalar_one_or_none()

    if not research:
        return

    # Create progress callback
    async def progress_callback(data: dict):
        await ws_manager.send_progress_update(research_id, data)

    # Create and run agent
    agent = ResearchAgent(
        db=db,
        llm_provider=settings.default_llm_provider,
        progress_callback=progress_callback,
    )

    try:
        results = await agent.run(research)

        # Send completion notification
        await ws_manager.send_progress_update(research_id, {
            "type": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "results": results,
        })

    except Exception as e:
        # Send error notification
        await ws_manager.send_progress_update(research_id, {
            "type": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        })

        # Update research status
        research.status = ResearchStatus.FAILED
        await db.commit()


@router.post("/{research_id}/run-agent", response_model=ResearchResponse)
async def run_agent_research(
    research_id: str,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Run autonomous agent research.

    This endpoint starts an AI agent that autonomously conducts research by:
    - Creating a research plan
    - Searching for information
    - Analyzing data
    - Making decisions about next steps
    - Saving findings
    - Generating a comprehensive report

    Progress updates are sent via WebSocket.
    """
    # Get research
    result = await db.execute(
        select(Research).where(Research.id == research_id, Research.user_id == current_user.id)
    )
    research = result.scalar_one_or_none()

    if not research:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research not found",
        )

    if research.status not in [ResearchStatus.CREATED, ResearchStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Research is already {research.status.value}. Create a new research to run agent.",
        )

    # Update status
    research.status = ResearchStatus.COLLECTING_DATA
    await db.commit()

    # Start agent in background
    background_tasks.add_task(_run_agent_research, str(research.id), db)

    return research


@router.websocket("/ws/{research_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    research_id: str,
):
    """
    WebSocket endpoint for real-time agent progress updates.

    Connect to this endpoint to receive real-time updates about agent progress.

    Example messages:
    {
        "timestamp": "2024-01-01T12:00:00",
        "message": "Step 1/20: Reasoning...",
        "state": {
            "research_id": "...",
            "step_count": 1,
            "findings_count": 0,
            ...
        }
    }
    """
    await ws_manager.connect(websocket, research_id)
    try:
        # Keep connection alive
        while True:
            # Receive messages from client (e.g., ping/pong)
            data = await websocket.receive_text()

            # Handle client messages if needed
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, research_id)
