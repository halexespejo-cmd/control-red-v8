"""
Tests for API endpoints
Author: Héctor Alejandro Pérez (@halexespejo-cmd)
"""
import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime

from src.models.database import Device


@pytest.mark.unit
class TestDevicesAPI:
    """Unit tests for /api/devices endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_devices_empty(self, test_client, db_session):
        """Test GET /api/devices with no devices"""
        # Override get_db dependency
        from src.main import app
        from src.models.database import get_db
        
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        response = await test_client.get("/api/devices/")
        
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 0
        assert data['blocked_count'] == 0
        assert len(data['devices']) == 0
        
        # Cleanup
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_get_devices_with_data(self, test_client, db_session):
        """Test GET /api/devices with devices in DB"""
        from src.main import app
        from src.models.database import get_db
        
        # Insert test devices
        device1 = Device(
            mac='AA:BB:CC:DD:EE:FF',
            ip='192.168.1.100',
            vendor='Apple, Inc.',
            category='laptop',
            is_blocked=False,
            is_self=False,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        device2 = Device(
            mac='11:22:33:44:55:66',
            ip='192.168.1.101',
            vendor='Samsung',
            category='phone',
            is_blocked=True,
            is_self=False,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        
        db_session.add(device1)
        db_session.add(device2)
        await db_session.commit()
        
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        response = await test_client.get("/api/devices/")
        
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 2
        assert data['blocked_count'] == 1
        
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_get_devices_filter_blocked(self, test_client, db_session):
        """Test GET /api/devices?blocked_only=true"""
        from src.main import app
        from src.models.database import get_db
        
        # Insert devices
        device_blocked = Device(
            mac='AA:BB:CC:DD:EE:FF',
            ip='192.168.1.100',
            is_blocked=True,
            is_self=False,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        device_active = Device(
            mac='11:22:33:44:55:66',
            ip='192.168.1.101',
            is_blocked=False,
            is_self=False,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        
        db_session.add_all([device_blocked, device_active])
        await db_session.commit()
        
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        response = await test_client.get("/api/devices/?blocked_only=true")
        
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 1
        assert data['devices'][0]['is_blocked'] is True
        
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_get_device_by_mac_found(self, test_client, db_session):
        """Test GET /api/devices/{mac} - found"""
        from src.main import app
        from src.models.database import get_db
        
        device = Device(
            mac='AA:BB:CC:DD:EE:FF',
            ip='192.168.1.100',
            vendor='Apple',
            is_blocked=False,
            is_self=False,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        db_session.add(device)
        await db_session.commit()
        
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        response = await test_client.get("/api/devices/AA:BB:CC:DD:EE:FF")
        
        assert response.status_code == 200
        data = response.json()
        assert data['mac'] == 'aa:bb:cc:dd:ee:ff'
        assert data['ip'] == '192.168.1.100'
        
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_get_device_by_mac_not_found(self, test_client, db_session):
        """Test GET /api/devices/{mac} - not found"""
        from src.main import app
        from src.models.database import get_db
        
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        response = await test_client.get("/api/devices/FF:FF:FF:FF:FF:FF")
        
        assert response.status_code == 404
        
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_update_device(self, test_client, db_session):
        """Test PATCH /api/devices/{mac}"""
        from src.main import app
        from src.models.database import get_db
        
        device = Device(
            mac='AA:BB:CC:DD:EE:FF',
            ip='192.168.1.100',
            is_blocked=False,
            is_self=False,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        db_session.add(device)
        await db_session.commit()
        
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        response = await test_client.patch(
            "/api/devices/AA:BB:CC:DD:EE:FF",
            json={'custom_name': 'My Laptop', 'category': 'laptop'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['custom_name'] == 'My Laptop'
        assert data['category'] == 'laptop'
        
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_block_device_success(self, test_client, db_session):
        """Test POST /api/devices/{mac}/block"""
        from src.main import app
        from src.models.database import get_db
        from src.services.arp_blocker import get_arp_blocker
        
        device = Device(
            mac='AA:BB:CC:DD:EE:FF',
            ip='192.168.1.100',
            is_blocked=False,
            is_self=False,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        db_session.add(device)
        await db_session.commit()
        
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Mock blocker
        with patch.object(get_arp_blocker(), 'is_initialized', True):
            with patch.object(get_arp_blocker(), 'block_device', return_value=True):
                response = await test_client.post("/api/devices/AA:BB:CC:DD:EE:FF/block")
        
        assert response.status_code == 200
        data = response.json()
        assert data['ok'] is True
        assert data['is_blocked'] is True
        
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_block_device_self_rejected(self, test_client, db_session):
        """Test blocking self/router is rejected"""
        from src.main import app
        from src.models.database import get_db
        
        device = Device(
            mac='AA:BB:CC:DD:EE:FF',
            ip='192.168.1.1',
            is_blocked=False,
            is_self=True,  # Router
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        db_session.add(device)
        await db_session.commit()
        
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        response = await test_client.post("/api/devices/AA:BB:CC:DD:EE:FF/block")
        
        assert response.status_code == 400
        assert "Cannot block self or router" in response.json()['detail']
        
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_unblock_device(self, test_client, db_session):
        """Test POST /api/devices/{mac}/unblock"""
        from src.main import app
        from src.models.database import get_db
        from src.services.arp_blocker import get_arp_blocker
        
        device = Device(
            mac='AA:BB:CC:DD:EE:FF',
            ip='192.168.1.100',
            is_blocked=True,
            is_self=False,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        db_session.add(device)
        await db_session.commit()
        
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Mock blocker
        with patch.object(get_arp_blocker(), 'is_initialized', True):
            with patch.object(get_arp_blocker(), 'unblock_device', return_value=True):
                response = await test_client.post("/api/devices/AA:BB:CC:DD:EE:FF/unblock")
        
        assert response.status_code == 200
        data = response.json()
        assert data['ok'] is True
        assert data['is_blocked'] is False
        
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_trigger_scan(self, test_client, db_session, mock_arp_scan_result, mock_network_info):
        """Test POST /api/devices/scan"""
        from src.main import app
        from src.models.database import get_db
        from src.services.scanner import NetworkScanner
        
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        with patch.object(NetworkScanner, 'full_scan', return_value={
            'scan_id': 1,
            'devices_found': 3,
            'duration': 2.5,
            'network': mock_network_info,
            'timestamp': '2026-10-16T10:00:00'
        }):
            response = await test_client.post("/api/devices/scan")
        
        assert response.status_code == 200
        data = response.json()
        assert data['ok'] is True
        assert data['scan_id'] == 1
        assert data['devices_found'] == 3
        
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_get_network_info(self, test_client, mock_network_info):
        """Test GET /api/devices/network/info"""
        from src.services.scanner import NetworkScanner
        
        with patch.object(NetworkScanner, 'get_network_info', return_value=mock_network_info):
            response = await test_client.get("/api/devices/network/info")
        
        assert response.status_code == 200
        data = response.json()
        assert data['ok'] is True
        assert data['gateway'] == '192.168.1.1'
        assert data['my_ip'] == '192.168.1.100'
    
    @pytest.mark.asyncio
    async def test_get_active_blocks(self, test_client):
        """Test GET /api/devices/blocked/active"""
        from src.services.arp_blocker import get_arp_blocker
        
        with patch.object(get_arp_blocker(), 'is_initialized', True):
            with patch.object(get_arp_blocker(), 'get_blocked_devices', return_value={
                'AA:BB:CC:DD:EE:FF': {
                    'ip': '192.168.1.100',
                    'active': True,
                    'blocked_at': '2026-10-16T10:00:00'
                }
            }):
                response = await test_client.get("/api/devices/blocked/active")
        
        assert response.status_code == 200
        data = response.json()
        assert data['ok'] is True
        assert data['count'] == 1
        assert 'AA:BB:CC:DD:EE:FF' in data['active_blocks']
