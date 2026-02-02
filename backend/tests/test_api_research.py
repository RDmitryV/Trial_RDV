"""Tests for research API endpoints."""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from app.models.user import User
from app.models.research import Research, ResearchStatus, ResearchType
from app.core.security import get_password_hash


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_research(db_session: AsyncSession, test_user: User) -> Research:
    """Create a test research."""
    research = Research(
        user_id=test_user.id,
        title="Test Market Research",
        product_description="Мобильное приложение для доставки еды",
        industry="Общественное питание",
        region="Москва",
        research_type=ResearchType.MARKET,
    )
    db_session.add(research)
    await db_session.commit()
    await db_session.refresh(research)
    return research


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create authentication headers for testing."""
    # This would normally create a real JWT token
    # For testing, we'll mock the authentication
    return {"Authorization": "Bearer test-token"}


@pytest.mark.asyncio
async def test_create_research_success(client: AsyncClient, auth_headers: dict):
    """Test successful research creation."""
    with patch('app.api.deps.get_current_active_user') as mock_auth:
        # Mock the authentication
        mock_user = User(
            id="test-user-id",
            email="test@example.com",
            is_active=True,
        )
        mock_auth.return_value = mock_user

        research_data = {
            "title": "New Market Research",
            "product_description": "Сервис доставки цветов",
            "industry": "Розничная торговля",
            "region": "Санкт-Петербург",
            "research_type": "market",
        }

        response = await client.post(
            "/api/v1/research/",
            json=research_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == research_data["title"]
        assert data["product_description"] == research_data["product_description"]
        assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_create_research_unauthorized(client: AsyncClient):
    """Test research creation without authentication."""
    research_data = {
        "title": "New Market Research",
        "product_description": "Test product",
        "industry": "Test industry",
        "region": "Test region",
        "research_type": "market",
    }

    response = await client.post("/api/v1/research/", json=research_data)

    # Should fail without authentication
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_researches(client: AsyncClient, test_user: User, test_research: Research, auth_headers: dict):
    """Test listing user's researches."""
    with patch('app.api.deps.get_current_active_user') as mock_auth:
        mock_auth.return_value = test_user

        response = await client.get("/api/v1/research/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["title"] == test_research.title


@pytest.mark.asyncio
async def test_list_researches_pagination(client: AsyncClient, test_user: User, auth_headers: dict):
    """Test research list pagination."""
    with patch('app.api.deps.get_current_active_user') as mock_auth:
        mock_auth.return_value = test_user

        response = await client.get(
            "/api/v1/research/?skip=0&limit=10",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10


@pytest.mark.asyncio
async def test_get_research_success(client: AsyncClient, test_user: User, test_research: Research, auth_headers: dict):
    """Test getting a specific research."""
    with patch('app.api.deps.get_current_active_user') as mock_auth:
        mock_auth.return_value = test_user

        response = await client.get(
            f"/api/v1/research/{test_research.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_research.id)
        assert data["title"] == test_research.title


@pytest.mark.asyncio
async def test_get_research_not_found(client: AsyncClient, test_user: User, auth_headers: dict):
    """Test getting a non-existent research."""
    with patch('app.api.deps.get_current_active_user') as mock_auth:
        mock_auth.return_value = test_user

        response = await client.get(
            "/api/v1/research/non-existent-id",
            headers=auth_headers,
        )

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_analyze_research_success(client: AsyncClient, test_user: User, test_research: Research, auth_headers: dict):
    """Test successful research analysis."""
    with patch('app.api.deps.get_current_active_user') as mock_auth, \
         patch('app.services.llm_service.LLMService') as mock_llm:
        mock_auth.return_value = test_user

        # Mock LLM service
        mock_llm_instance = AsyncMock()
        mock_llm_instance.analyze_market.return_value = "Detailed market analysis result..."
        mock_llm.return_value = mock_llm_instance

        response = await client.post(
            f"/api/v1/research/{test_research.id}/analyze",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["research_id"] == str(test_research.id)
        assert "analysis" in data
        assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_analyze_research_not_found(client: AsyncClient, test_user: User, auth_headers: dict):
    """Test analyzing a non-existent research."""
    with patch('app.api.deps.get_current_active_user') as mock_auth:
        mock_auth.return_value = test_user

        response = await client.post(
            "/api/v1/research/non-existent-id/analyze",
            headers=auth_headers,
        )

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_analyze_research_llm_failure(client: AsyncClient, test_user: User, test_research: Research, auth_headers: dict):
    """Test research analysis with LLM failure."""
    with patch('app.api.deps.get_current_active_user') as mock_auth, \
         patch('app.services.llm_service.LLMService') as mock_llm:
        mock_auth.return_value = test_user

        # Mock LLM service to raise exception
        mock_llm_instance = AsyncMock()
        mock_llm_instance.analyze_market.side_effect = Exception("LLM API error")
        mock_llm.return_value = mock_llm_instance

        response = await client.post(
            f"/api/v1/research/{test_research.id}/analyze",
            headers=auth_headers,
        )

        assert response.status_code == 500
        assert "Analysis failed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_research_validation_error(client: AsyncClient, auth_headers: dict):
    """Test research creation with invalid data."""
    with patch('app.api.deps.get_current_active_user') as mock_auth:
        mock_user = User(
            id="test-user-id",
            email="test@example.com",
            is_active=True,
        )
        mock_auth.return_value = mock_user

        # Missing required fields
        research_data = {
            "title": "Incomplete Research",
        }

        response = await client.post(
            "/api/v1/research/",
            json=research_data,
            headers=auth_headers,
        )

        assert response.status_code == 422  # Validation error
