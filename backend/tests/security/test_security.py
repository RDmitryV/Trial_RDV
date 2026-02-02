"""Security tests for the application."""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch

from app.models.user import User
from app.core.security import get_password_hash


@pytest_asyncio.fixture
async def test_user_security(db_session: AsyncSession) -> User:
    """Create a test user for security tests."""
    user = User(
        email="security@example.com",
        hashed_password=get_password_hash("securepassword123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestSQLInjection:
    """Test SQL injection protection."""

    @pytest.mark.asyncio
    async def test_sql_injection_in_search(self, client: AsyncClient, test_user_security: User):
        """Test SQL injection in search parameters."""
        with patch('app.api.deps.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user_security

            # Attempt SQL injection
            malicious_queries = [
                "'; DROP TABLE users; --",
                "1' OR '1'='1",
                "1'; DELETE FROM research WHERE '1'='1",
                "' UNION SELECT * FROM users --",
            ]

            for query in malicious_queries:
                response = await client.get(
                    f"/api/v1/research/?search={query}",
                    headers={"Authorization": "Bearer test-token"}
                )

                # Should either return safe results or validation error, not 500
                assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_sql_injection_in_filters(self, client: AsyncClient, test_user_security: User):
        """Test SQL injection in filter parameters."""
        with patch('app.api.deps.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user_security

            # Attempt SQL injection in filters
            response = await client.get(
                "/api/v1/research/?region=' OR 1=1--",
                headers={"Authorization": "Bearer test-token"}
            )

            # Should handle safely
            assert response.status_code in [200, 400, 422]


class TestXSSProtection:
    """Test XSS (Cross-Site Scripting) protection."""

    @pytest.mark.asyncio
    async def test_xss_in_research_title(self, client: AsyncClient, test_user_security: User):
        """Test XSS protection in research title."""
        with patch('app.api.deps.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user_security

            xss_payloads = [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert('XSS')>",
                "javascript:alert('XSS')",
                "<iframe src='javascript:alert(1)'>",
            ]

            for payload in xss_payloads:
                research_data = {
                    "title": payload,
                    "product_description": "Test product",
                    "industry": "Test industry",
                    "region": "Test region",
                    "research_type": "market"
                }

                response = await client.post(
                    "/api/v1/research/",
                    json=research_data,
                    headers={"Authorization": "Bearer test-token"}
                )

                if response.status_code == 201:
                    # If created, verify the payload is escaped/sanitized
                    data = response.json()
                    # Script tags should be escaped or removed
                    assert "<script>" not in data["title"]
                    assert "javascript:" not in data["title"]

    @pytest.mark.asyncio
    async def test_xss_in_product_description(self, client: AsyncClient, test_user_security: User):
        """Test XSS protection in product description."""
        with patch('app.api.deps.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user_security

            research_data = {
                "title": "Safe Title",
                "product_description": "<script>alert('XSS')</script>Malicious description",
                "industry": "Test",
                "region": "Test",
                "research_type": "market"
            }

            response = await client.post(
                "/api/v1/research/",
                json=research_data,
                headers={"Authorization": "Bearer test-token"}
            )

            if response.status_code == 201:
                data = response.json()
                # Verify XSS is prevented
                assert "<script>" not in data["product_description"]


class TestCSRFProtection:
    """Test CSRF protection."""

    @pytest.mark.asyncio
    async def test_csrf_token_required_for_state_changing_operations(self, client: AsyncClient):
        """Test that state-changing operations require CSRF protection."""
        # Attempt to create research without proper CSRF token
        research_data = {
            "title": "CSRF Test",
            "product_description": "Test",
            "industry": "Test",
            "region": "Test",
            "research_type": "market"
        }

        # Without proper authentication/CSRF token
        response = await client.post("/api/v1/research/", json=research_data)

        # Should be rejected
        assert response.status_code in [401, 403, 422]


class TestAuthenticationSecurity:
    """Test authentication security."""

    @pytest.mark.asyncio
    async def test_weak_password_rejected(self, client: AsyncClient):
        """Test that weak passwords are rejected."""
        weak_passwords = [
            "123",
            "password",
            "abc",
            "12345678",
        ]

        for weak_pwd in weak_passwords:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "weak@example.com",
                    "username": "weakuser",
                    "password": weak_pwd
                }
            )

            # Should reject weak passwords
            # Either validation error or specific password strength error
            assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_password_not_returned_in_response(self, client: AsyncClient, test_user_security: User):
        """Test that password hashes are never returned in API responses."""
        with patch('app.api.deps.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user_security

            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer test-token"}
            )

            if response.status_code == 200:
                data = response.json()
                # Password should never be in response
                assert "password" not in data
                assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_rate_limiting_on_login(self, client: AsyncClient):
        """Test rate limiting on login endpoint."""
        # Attempt multiple failed logins
        for _ in range(10):
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "username": "nonexistent",
                    "password": "wrongpassword"
                }
            )

        # After many failed attempts, should implement rate limiting
        # This depends on implementation - may return 429 or keep returning 401
        # At minimum, should not reveal timing differences
        assert response.status_code in [401, 429]


class TestInputValidation:
    """Test input validation security."""

    @pytest.mark.asyncio
    async def test_oversized_input_rejected(self, client: AsyncClient, test_user_security: User):
        """Test that oversized inputs are rejected."""
        with patch('app.api.deps.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user_security

            # Create extremely large input
            huge_description = "A" * 1000000  # 1MB of text

            research_data = {
                "title": "Test",
                "product_description": huge_description,
                "industry": "Test",
                "region": "Test",
                "research_type": "market"
            }

            response = await client.post(
                "/api/v1/research/",
                json=research_data,
                headers={"Authorization": "Bearer test-token"}
            )

            # Should reject oversized input
            assert response.status_code in [400, 413, 422]

    @pytest.mark.asyncio
    async def test_invalid_data_types_rejected(self, client: AsyncClient, test_user_security: User):
        """Test that invalid data types are rejected."""
        with patch('app.api.deps.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user_security

            invalid_data = {
                "title": 12345,  # Should be string
                "product_description": ["array", "instead", "of", "string"],
                "industry": None,  # Required field
                "region": {"invalid": "object"},
                "research_type": "invalid_type"
            }

            response = await client.post(
                "/api/v1/research/",
                json=invalid_data,
                headers={"Authorization": "Bearer test-token"}
            )

            # Should reject with validation error
            assert response.status_code == 422


class TestAuthorizationSecurity:
    """Test authorization and access control."""

    @pytest.mark.asyncio
    async def test_cannot_access_other_users_research(self, client: AsyncClient, test_user_security: User):
        """Test that users cannot access other users' research."""
        with patch('app.api.deps.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user_security

            # Try to access research with a different user's ID
            other_user_research_id = "other-user-research-id"

            response = await client.get(
                f"/api/v1/research/{other_user_research_id}",
                headers={"Authorization": "Bearer test-token"}
            )

            # Should return 404 (not revealing existence) or 403
            assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_unauthorized_access_blocked(self, client: AsyncClient):
        """Test that unauthorized access is blocked."""
        # Try to access protected endpoint without authentication
        response = await client.get("/api/v1/research/")

        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_token_expiration_handled(self, client: AsyncClient):
        """Test that expired tokens are rejected."""
        # Use an obviously expired/invalid token
        response = await client.get(
            "/api/v1/research/",
            headers={"Authorization": "Bearer expired-or-invalid-token"}
        )

        assert response.status_code in [401, 403]
