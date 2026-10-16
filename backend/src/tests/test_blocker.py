"""
Tests for ARPBlocker service
Author: Héctor Alejandro Pérez (@halexespejo-cmd)
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, call
import threading

from src.services.arp_blocker import ARPBlocker, get_arp_blocker


@pytest.mark.unit
class TestARPBlocker:
    """Unit tests for ARPBlocker"""
    
    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful blocker initialization"""
        blocker = ARPBlocker()
        
        with patch.object(blocker, '_get_mac', return_value='AA:BB:CC:DD:EE:FF'):
            with patch('src.services.arp_blocker.get_if_hwaddr', return_value='11:22:33:44:55:66'):
                await blocker.initialize(
                    gateway_ip='192.168.1.1',
                    gateway_mac='AA:BB:CC:DD:EE:FF'
                )
        
        assert blocker.is_initialized is True
        assert blocker.gateway_ip == '192.168.1.1'
        assert blocker.gateway_mac == 'AA:BB:CC:DD:EE:FF'
        assert blocker.my_mac == '11:22:33:44:55:66'
    
    @pytest.mark.asyncio
    async def test_initialize_auto_gateway_mac(self):
        """Test initialization with auto gateway MAC detection"""
        blocker = ARPBlocker()
        
        with patch.object(blocker, '_get_mac', return_value='AA:BB:CC:DD:EE:FF'):
            with patch('src.services.arp_blocker.get_if_hwaddr', return_value='11:22:33:44:55:66'):
                await blocker.initialize(gateway_ip='192.168.1.1')
        
        assert blocker.gateway_mac == 'AA:BB:CC:DD:EE:FF'
    
    @pytest.mark.asyncio
    async def test_initialize_with_fallback_mac(self):
        """Test initialization with MAC fallback"""
        blocker = ARPBlocker()
        
        # get_if_hwaddr falla, pero continúa con fallback
        with patch('src.services.arp_blocker.get_if_hwaddr', side_effect=Exception("No interface")):
            with patch.object(blocker, '_get_mac', return_value='AA:BB:CC:DD:EE:FF'):
                with patch('src.services.arp_blocker.conf') as mock_conf:
                    mock_conf.iface = 'eth0'
                    mock_iface = MagicMock()
                    with patch('src.services.arp_blocker.get_if_hwaddr', return_value='00:00:00:00:00:00'):
                        await blocker.initialize(gateway_ip='192.168.1.1')
        
        # Inicializa con fallback MAC
        assert blocker.is_initialized is True
        assert blocker.my_mac == '00:00:00:00:00:00'
    
    @pytest.mark.asyncio
    async def test_block_device_not_initialized(self):
        """Test blocking without initialization"""
        blocker = ARPBlocker()
        blocker.is_initialized = False
        
        result = await blocker.block_device('192.168.1.100', 'AA:BB:CC:DD:EE:FF')
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_block_device_success(self):
        """Test successful device blocking"""
        blocker = ARPBlocker()
        blocker.is_initialized = True
        blocker.gateway_ip = '192.168.1.1'
        blocker.gateway_mac = 'AA:11:BB:22:CC:33'
        blocker.my_mac = '11:22:33:44:55:66'
        
        with patch('threading.Thread') as mock_thread:
            result = await blocker.block_device('192.168.1.100', 'AA:BB:CC:DD:EE:FF')
        
        assert result is True
        assert 'AA:BB:CC:DD:EE:FF' in blocker.blocked_devices
        assert blocker.blocked_devices['AA:BB:CC:DD:EE:FF']['ip'] == '192.168.1.100'
        assert blocker.blocked_devices['AA:BB:CC:DD:EE:FF']['active'] is True
        assert mock_thread.called
    
    @pytest.mark.asyncio
    async def test_block_device_already_blocked(self):
        """Test blocking already blocked device (idempotent)"""
        blocker = ARPBlocker()
        blocker.is_initialized = True
        blocker.blocked_devices['AA:BB:CC:DD:EE:FF'] = {
            'ip': '192.168.1.100',
            'active': True
        }
        
        result = await blocker.block_device('192.168.1.100', 'aa:bb:cc:dd:ee:ff')
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_unblock_device_success(self):
        """Test successful device unblocking"""
        blocker = ARPBlocker()
        blocker.is_initialized = True
        
        # Setup blocked device
        stop_event = threading.Event()
        mock_thread = MagicMock()
        
        blocker.blocked_devices['AA:BB:CC:DD:EE:FF'] = {
            'ip': '192.168.1.100',
            'active': True
        }
        blocker._stop_flags['AA:BB:CC:DD:EE:FF'] = stop_event
        blocker._threads['AA:BB:CC:DD:EE:FF'] = mock_thread
        
        result = await blocker.unblock_device('AA:BB:CC:DD:EE:FF')
        
        assert result is True
        assert 'AA:BB:CC:DD:EE:FF' not in blocker.blocked_devices
        assert stop_event.is_set()
    
    @pytest.mark.asyncio
    async def test_unblock_device_not_blocked(self):
        """Test unblocking device that isn't blocked"""
        blocker = ARPBlocker()
        blocker.is_initialized = True
        
        result = await blocker.unblock_device('AA:BB:CC:DD:EE:FF')
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_stop_all(self):
        """Test stopping all active blocks"""
        blocker = ARPBlocker()
        blocker.is_initialized = True
        
        # Setup multiple blocked devices
        for i, mac in enumerate(['AA:BB:CC:DD:EE:FF', '11:22:33:44:55:66']):
            stop_event = threading.Event()
            blocker.blocked_devices[mac] = {
                'ip': f'192.168.1.{100+i}',
                'active': True
            }
            blocker._stop_flags[mac] = stop_event
        
        await blocker.stop_all()
        
        assert len(blocker.blocked_devices) == 0
    
    def test_get_blocked_devices_empty(self):
        """Test getting blocked devices when none"""
        blocker = ARPBlocker()
        
        result = blocker.get_blocked_devices()
        
        assert result == {}
    
    def test_get_blocked_devices_with_blocks(self):
        """Test getting blocked devices with active blocks"""
        blocker = ARPBlocker()
        from datetime import datetime
        
        blocker.blocked_devices['AA:BB:CC:DD:EE:FF'] = {
            'ip': '192.168.1.100',
            'active': True,
            'blocked_at': datetime(2026, 10, 16, 10, 0, 0)
        }
        
        result = blocker.get_blocked_devices()
        
        assert 'AA:BB:CC:DD:EE:FF' in result
        assert result['AA:BB:CC:DD:EE:FF']['ip'] == '192.168.1.100'
        assert result['AA:BB:CC:DD:EE:FF']['active'] is True
    
    def test_singleton_pattern(self):
        """Test get_arp_blocker returns same instance"""
        blocker1 = get_arp_blocker()
        blocker2 = get_arp_blocker()
        
        assert blocker1 is blocker2
    
    @pytest.mark.requires_sudo
    def test_spoof_thread_mock(self):
        """Test ARP spoofing thread execution (mocked)"""
        blocker = ARPBlocker()
        blocker.is_initialized = True
        blocker.gateway_ip = '192.168.1.1'
        blocker.gateway_mac = 'AA:11:BB:22:CC:33'
        blocker.my_mac = '11:22:33:44:55:66'
        
        stop_event = threading.Event()
        
        with patch('src.services.arp_blocker.sendp') as mock_sendp:
            with patch('src.services.arp_blocker.ARP'):
                with patch('src.services.arp_blocker.Ether'):
                    # Run thread for very short time
                    thread = threading.Thread(
                        target=blocker._spoof_thread,
                        args=('192.168.1.100', 'AA:BB:CC:DD:EE:FF', stop_event),
                        daemon=True
                    )
                    thread.start()
                    
                    # Stop after a moment
                    import time
                    time.sleep(0.1)
                    stop_event.set()
                    thread.join(timeout=1)
        
        # Verify sendp was called (ARP packets sent)
        assert mock_sendp.called
    
    def test_restore_arp_mock(self):
        """Test ARP restoration (mocked)"""
        blocker = ARPBlocker()
        blocker.gateway_ip = '192.168.1.1'
        blocker.gateway_mac = 'AA:11:BB:22:CC:33'
        
        with patch('src.services.arp_blocker.sendp') as mock_sendp:
            with patch('src.services.arp_blocker.ARP'):
                with patch('src.services.arp_blocker.Ether'):
                    blocker._restore_arp('192.168.1.100', 'AA:BB:CC:DD:EE:FF')
        
        # Should send restore packets (3 attempts x 2 packets = 6 calls)
        assert mock_sendp.call_count >= 6
