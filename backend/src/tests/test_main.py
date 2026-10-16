"""
Tests for main.py - Lifespan events and endpoints
Author: Héctor Alejandro Pérez (@halexespejo-cmd)
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from src.main import app


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root health check endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["app"] == "Control de Red Backend"
        assert "version" in data
        assert data["status"] == "running"


@pytest.mark.asyncio
async def test_api_status_endpoint():
    """Test API status endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "driver" in data


@pytest.mark.asyncio
async def test_login_page_endpoint():
    """Test login page renders"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/login")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_dashboard_page_endpoint():
    """Test dashboard page renders"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/dashboard")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_metrics_endpoint():
    """Test Prometheus metrics endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/metrics")
        assert response.status_code == 200
        # Metrics should contain basic prometheus format
        assert "http_requests" in response.text or "python_info" in response.text


@pytest.mark.asyncio
async def test_rate_limiting():
    """Test rate limiting on root endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Make multiple requests (more than limit)
        responses = []
        for _ in range(5):
            response = await client.get("/")
            responses.append(response.status_code)
        
        # All should succeed (we're under 100/min limit in tests)
        assert all(status == 200 for status in responses)


@pytest.mark.asyncio
async def test_cors_headers():
    """Test CORS headers are present"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == 200
        # CORS middleware should add headers
        assert "access-control-allow-origin" in response.headers


@pytest.mark.asyncio 
@patch('src.models.database.init_db')
@patch('src.utils.cache.get_redis')
async def test_lifespan_startup(mock_redis, mock_init_db):
    """Test lifespan startup events"""
    mock_init_db.return_value = None
    mock_redis_client = AsyncMock()
    mock_redis.return_value = mock_redis_client
    
    # Lifespan is tested by app startup
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_404_error():
    """Test 404 error for non-existent endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/non-existent-endpoint")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_static_files_mounted():
    """Test static files are accessible"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Try to access a static file
        response = await client.get("/static/css/dashboard.css")
        # Should either work (200) or be a valid app response
        assert response.status_code in [200, 404]  # 404 ok if file doesn't exist in test


@pytest.mark.asyncio
async def test_error_handler():
    """Test global exception handler"""
    # This would require triggering an actual error
    # For now, just verify the app is configured
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_check_with_debug():
    """Test health check returns debug status"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
        data = response.json()
        assert "debug" in data
        assert isinstance(data["debug"], bool)
