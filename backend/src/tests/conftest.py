"""
Pytest configuration and fixtures
Author: Héctor Alejandro Pérez (@halexespejo-cmd)
"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient, ASGITransport

from src.models.database import Base


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test
    """
    # Create async engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    # Drop tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create HTTP client for API tests
    """
    from src.main import app as _app
    async with AsyncClient(transport=ASGITransport(app=_app), base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_network_info():
    """Mock network info data"""
    return {
        'gateway': '192.168.1.1',
        'my_ip': '192.168.1.100',
        'ssid': 'TestNetwork',
        'network_range': '192.168.1.0/24',
        'public_ip': '203.0.113.1'
    }


@pytest.fixture
def mock_arp_scan_result():
    """Mock ARP scan result"""
    return [
        {
            'ip': '192.168.1.1',
            'mac': 'AA:BB:CC:DD:EE:FF',
            'vendor': 'Cisco Systems',
            'hostname': 'router.local',
            'scan_method': 'arp'
        },
        {
            'ip': '192.168.1.10',
            'mac': '11:22:33:44:55:66',
            'vendor': 'Apple, Inc.',
            'hostname': 'iPhone-User',
            'scan_method': 'arp'
        },
        {
            'ip': '192.168.1.20',
            'mac': 'AA:11:BB:22:CC:33',
            'vendor': 'Amazon Technologies',
            'hostname': 'echo-Living',
            'scan_method': 'arp'
        }
    ]


@pytest.fixture
def sample_device_data():
    """Sample device data for testing"""
    return {
        'mac': 'AA:BB:CC:DD:EE:FF',
        'ip': '192.168.1.100',
        'vendor': 'Apple, Inc.',
        'hostname': 'MacBook-Pro',
        'category': 'laptop',
        'is_blocked': False,
        'is_self': False
    }
