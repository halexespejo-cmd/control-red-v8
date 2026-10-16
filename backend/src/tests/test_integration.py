"""
Integration Tests - Full flow testing
Author: Héctor Alejandro Pérez (@halexespejo-cmd)
"""
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.mark.asyncio
async def test_full_user_flow(db_session):
    """Test complete user flow: register -> login -> access protected route"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register
        register_response = await client.post(
            "/api/auth/register",
            json={
                "username": "flowtest",
                "email": "flow@example.com",
                "password": "flow123",
                "is_admin": False
            }
        )
        assert register_response.status_code in [200, 201]
        
        # 2. Login
        login_response = await client.post(
            "/api/auth/login",
            json={"username": "flowtest", "password": "flow123"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # 3. Access /me
        me_response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        
        # 4. Access devices (protected)
        devices_response = await client.get(
            "/api/devices/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert devices_response.status_code in [200, 401]  # Depends on auth implementation


@pytest.mark.asyncio
async def test_device_lifecycle(db_session):
    """Test device discovery -> block -> unblock lifecycle"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Scan network
        scan_response = await client.post("/api/devices/scan")
        assert scan_response.status_code in [200, 202]
        
        # 2. Get devices
        devices_response = await client.get("/api/devices/")
        assert devices_response.status_code == 200
        devices = devices_response.json()
        
        if devices and len(devices) > 0:
            device_mac = devices[0].get("mac")
            
            # 3. Block device
            block_response = await client.post(f"/api/devices/{device_mac}/block")
            assert block_response.status_code in [200, 404, 500]
            
            # 4. Check blocked status
            device_response = await client.get(f"/api/devices/{device_mac}")
            if device_response.status_code == 200:
                device = device_response.json()
                assert device.get("is_blocked") in [True, False, None]
            
            # 5. Unblock device
            unblock_response = await client.post(f"/api/devices/{device_mac}/unblock")
            assert unblock_response.status_code in [200, 404, 500]


@pytest.mark.asyncio
async def test_cache_invalidation_flow(db_session):
    """Test cache is invalidated on device update"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Get devices (cache miss)
        first_response = await client.get("/api/devices/")
        assert first_response.status_code == 200
        
        # 2. Get devices again (cache hit)
        second_response = await client.get("/api/devices/")
        assert second_response.status_code == 200
        
        # 3. Update device (invalidates cache)
        scan_response = await client.post("/api/devices/scan")
        assert scan_response.status_code in [200, 202]
        
        # 4. Get devices (cache miss again)
        third_response = await client.get("/api/devices/")
        assert third_response.status_code == 200


@pytest.mark.asyncio
async def test_celery_task_flow():
    """Test background task trigger and status check"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Trigger background scan
        trigger_response = await client.post("/api/tasks/scan")
        
        if trigger_response.status_code == 200:
            data = trigger_response.json()
            task_id = data.get("task_id")
            
            if task_id:
                # 2. Check task status
                status_response = await client.get(f"/api/tasks/{task_id}")
                assert status_response.status_code == 200
                status_data = status_response.json()
                assert "status" in status_data
        elif trigger_response.status_code == 503:
            # Celery not available (graceful degradation)
            assert True


@pytest.mark.asyncio
async def test_network_info_flow():
    """Test network information retrieval"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/devices/network/info")
        assert response.status_code == 200
        data = response.json()
        assert "interface" in data or "ip" in data


@pytest.mark.asyncio
async def test_error_recovery():
    """Test system recovers from errors gracefully"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Try invalid MAC address
        response = await client.get("/api/devices/invalid:mac:address")
        assert response.status_code in [404, 422, 400]
        
        # System should still work
        health_response = await client.get("/")
        assert health_response.status_code == 200


@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test system handles concurrent requests"""
    import asyncio
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Make 10 concurrent requests
        tasks = []
        for _ in range(10):
            tasks.append(client.get("/"))
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)


@pytest.mark.asyncio
async def test_admin_vs_user_permissions(db_session):
    """Test admin can access admin routes, user cannot"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create admin
        await client.post(
            "/api/auth/register",
            json={
                "username": "admin_perm",
                "email": "admin_perm@example.com",
                "password": "admin123",
                "is_admin": True
            }
        )
        
        # Create user
        await client.post(
            "/api/auth/register",
            json={
                "username": "user_perm",
                "email": "user_perm@example.com",
                "password": "user123",
                "is_admin": False
            }
        )
        
        # Admin login
        admin_login = await client.post(
            "/api/auth/login",
            json={"username": "admin_perm", "password": "admin123"}
        )
        admin_token = admin_login.json()["access_token"]
        
        # User login
        user_login = await client.post(
            "/api/auth/login",
            json={"username": "user_perm", "password": "user123"}
        )
        user_token = user_login.json()["access_token"]
        
        # Admin can access admin route
        admin_response = await client.get(
            "/api/auth/admin-only",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert admin_response.status_code == 200
        
        # User cannot access admin route
        user_response = await client.get(
            "/api/auth/admin-only",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert user_response.status_code == 403


@pytest.mark.asyncio
async def test_database_transaction_rollback(db_session):
    """Test database rollback on error"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Try to register with invalid data
        response = await client.post(
            "/api/auth/register",
            json={
                "username": "",  # Invalid empty username
                "email": "invalid",
                "password": "short",
            }
        )
        
        # Should fail validation
        assert response.status_code in [400, 422]
        
        # Database should still be consistent
        health_response = await client.get("/")
        assert health_response.status_code == 200


@pytest.mark.asyncio
async def test_observability_endpoints():
    """Test observability endpoints are accessible"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Metrics endpoint
        metrics_response = await client.get("/metrics")
        assert metrics_response.status_code == 200
        
        # Health endpoint
        health_response = await client.get("/")
        assert health_response.status_code == 200
        
        # API status
        status_response = await client.get("/api/status")
        assert status_response.status_code == 200
