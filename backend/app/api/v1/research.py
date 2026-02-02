"""Research endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.research import Research, ResearchStatus, ResearchType
from app.services.llm_service import LLMService

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
    """Analyze research using LLM."""
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
        # Perform analysis using LLM
        analysis_result = await llm_service.analyze_market(
            product_description=research.product_description,
            industry=research.industry,
            region=research.region,
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
