"""
Tests for auth.py - Admin routes and edge cases
Author: Héctor Alejandro Pérez (@halexespejo-cmd)
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from src.main import app
from src.models.user import User
from src.utils.auth import get_password_hash, create_access_token


@pytest.mark.asyncio
async def test_register_user_success(db_session):
    """Test user registration success"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "securepass123",
                "is_admin": False
            }
        )
        assert response.status_code in [201, 200]
        data = response.json()
        assert "username" in data or "email" in data


@pytest.mark.asyncio
async def test_register_duplicate_username(db_session):
    """Test registration fails with duplicate username"""
    # Register first user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/api/auth/register",
            json={
                "username": "duplicate",
                "email": "user1@example.com",
                "password": "pass123",
            }
        )
        
        # Try duplicate username
        response = await client.post(
            "/api/auth/register",
            json={
                "username": "duplicate",
                "email": "user2@example.com",
                "password": "pass456",
            }
        )
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_duplicate_email(db_session):
    """Test registration fails with duplicate email"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/api/auth/register",
            json={
                "username": "user1",
                "email": "same@example.com",
                "password": "pass123",
            }
        )
        
        response = await client.post(
            "/api/auth/register",
            json={
                "username": "user2",
                "email": "same@example.com",
                "password": "pass456",
            }
        )
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_success(db_session):
    """Test successful login"""
    # Register user first
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/api/auth/register",
            json={
                "username": "logintest",
                "email": "login@example.com",
                "password": "password123",
            }
        )
        
        # Login
        response = await client.post(
            "/api/auth/login",
            json={
                "username": "logintest",
                "password": "password123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(db_session):
    """Test login fails with wrong password"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/api/auth/register",
            json={
                "username": "wrongpass",
                "email": "wrong@example.com",
                "password": "correct123",
            }
        )
        
        response = await client.post(
            "/api/auth/login",
            json={
                "username": "wrongpass",
                "password": "wrong123"
            }
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user():
    """Test login fails for non-existent user"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            json={
                "username": "doesnotexist",
                "password": "anypass"
            }
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(db_session):
    """Test /me endpoint with valid token"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register and login
        await client.post(
            "/api/auth/register",
            json={
                "username": "metest",
                "email": "me@example.com",
                "password": "pass123",
            }
        )
        
        login_response = await client.post(
            "/api/auth/login",
            json={"username": "metest", "password": "pass123"}
        )
        token = login_response.json()["access_token"]
        
        # Get /me
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "username" in data or "sub" in data


@pytest.mark.asyncio
async def test_get_me_no_token():
    """Test /me endpoint without token"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/auth/me")
        assert response.status_code == 403  # No auth header


@pytest.mark.asyncio
async def test_get_me_invalid_token():
    """Test /me endpoint with invalid token"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_only_route_as_admin(db_session):
    """Test admin route with admin user"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register admin
        await client.post(
            "/api/auth/register",
            json={
                "username": "admin",
                "email": "admin@example.com",
                "password": "admin123",
                "is_admin": True
            }
        )
        
        # Login
        login_response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]
        
        # Access admin route
        response = await client.get(
            "/api/auth/admin-only",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_only_route_as_user(db_session):
    """Test admin route with regular user"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register regular user
        await client.post(
            "/api/auth/register",
            json={
                "username": "regularuser",
                "email": "user@example.com",
                "password": "user123",
                "is_admin": False
            }
        )
        
        # Login
        login_response = await client.post(
            "/api/auth/login",
            json={"username": "regularuser", "password": "user123"}
        )
        token = login_response.json()["access_token"]
        
        # Try admin route
        response = await client.get(
            "/api/auth/admin-only",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_token_expiration():
    """Test token includes expiration"""
    from src.utils.auth import create_access_token
    import jwt
    from src.config import get_settings
    
    settings = get_settings()
    token = create_access_token({"sub": "testuser"})
    
    # Decode without verification to check payload
    payload = jwt.decode(token, options={"verify_signature": False})
    assert "exp" in payload


@pytest.mark.asyncio
async def test_password_hashing():
    """Test password is properly hashed"""
    from src.utils.auth import get_password_hash, verify_password
    
    password = "mysecretpass"
    hashed = get_password_hash(password)
    
    # Hash should be different from plain
    assert hashed != password
    # Verify should work
    assert verify_password(password, hashed) is True
    # Wrong password should fail
    assert verify_password("wrongpass", hashed) is False
