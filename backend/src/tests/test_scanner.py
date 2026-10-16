"""
Tests for NetworkScanner service
Author: Héctor Alejandro Pérez (@halexespejo-cmd)
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from src.services.scanner import NetworkScanner
from src.models.database import Device, NetworkScan


@pytest.mark.unit
class TestNetworkScanner:
    """Unit tests for NetworkScanner"""
    
    @pytest.mark.asyncio
    async def test_get_network_info_success(self, mock_network_info):
        """Test successful network info retrieval"""
        scanner = NetworkScanner()
        
        with patch.object(scanner, '_get_network_info_sync', return_value=mock_network_info):
            result = await scanner.get_network_info()
        
        assert result['gateway'] == '192.168.1.1'
        assert result['my_ip'] == '192.168.1.100'
        assert result['network_range'] == '192.168.1.0/24'
        assert scanner.gateway == '192.168.1.1'
        assert scanner.my_ip == '192.168.1.100'
    
    @pytest.mark.asyncio
    async def test_get_network_info_failure(self):
        """Test network info retrieval failure handling"""
        scanner = NetworkScanner()
        
        with patch.object(scanner, '_get_network_info_sync', side_effect=Exception("Network error")):
            result = await scanner.get_network_info()
        
        assert result['gateway'] is None
        assert result['my_ip'] is None
        assert result['network_range'] is None
    
    @pytest.mark.asyncio
    async def test_scan_arp_success(self, mock_arp_scan_result):
        """Test successful ARP scan"""
        scanner = NetworkScanner()
        
        with patch.object(scanner, '_arp_scan_sync', return_value=mock_arp_scan_result):
            with patch.object(scanner, 'get_network_info', return_value={'network_range': '192.168.1.0/24'}):
                result = await scanner.scan_arp()
        
        assert len(result) == 3
        assert result[0]['ip'] == '192.168.1.1'
        assert result[0]['mac'] == 'AA:BB:CC:DD:EE:FF'
        assert result[1]['vendor'] == 'Apple, Inc.'
    
    @pytest.mark.asyncio
    async def test_scan_arp_with_custom_target(self, mock_arp_scan_result):
        """Test ARP scan with custom target range"""
        scanner = NetworkScanner()
        
        with patch.object(scanner, '_arp_scan_sync', return_value=mock_arp_scan_result):
            result = await scanner.scan_arp(target='10.0.0.0/24')
        
        assert len(result) == 3
    
    @pytest.mark.asyncio
    async def test_scan_arp_failure(self):
        """Test ARP scan failure handling"""
        scanner = NetworkScanner()
        
        with patch.object(scanner, '_arp_scan_sync', side_effect=Exception("Scan error")):
            with patch.object(scanner, 'get_network_info', return_value={'network_range': '192.168.1.0/24'}):
                result = await scanner.scan_arp()
        
        assert result == []
    
    def test_get_vendor_known(self):
        """Test vendor lookup for known OUI"""
        scanner = NetworkScanner()
        
        # Test known vendor
        vendor = scanner._get_vendor('C4:EB:FF:11:22:33')
        assert vendor == 'ZTE Corporation'
        
        vendor = scanner._get_vendor('28:10:7B:AA:BB:CC')
        assert vendor == 'Amazon Technologies'
    
    def test_get_vendor_unknown(self):
        """Test vendor lookup for unknown OUI"""
        scanner = NetworkScanner()
        
        vendor = scanner._get_vendor('99:99:99:11:22:33')
        assert vendor == 'Unknown Vendor'
    
    def test_get_hostname_success(self):
        """Test hostname lookup success"""
        scanner = NetworkScanner()
        
        with patch('socket.gethostbyaddr', return_value=('test-device.local', [], [])):
            hostname = scanner._get_hostname('192.168.1.100')
        
        assert hostname == 'test-device.local'
    
    def test_get_hostname_failure(self):
        """Test hostname lookup failure"""
        scanner = NetworkScanner()
        
        with patch('socket.gethostbyaddr', side_effect=Exception("No hostname")):
            hostname = scanner._get_hostname('192.168.1.100')
        
        assert hostname is None
    
    @pytest.mark.asyncio
    async def test_categorize_device_router(self):
        """Test device categorization - router"""
        scanner = NetworkScanner()
        scanner.gateway = '192.168.1.1'
        
        device = {
            'ip': '192.168.1.1',
            'vendor': 'Cisco Systems',
            'hostname': 'router',
            'mac': 'AA:BB:CC:DD:EE:FF'
        }
        
        category = await scanner.categorize_device(device)
        assert category == 'router'
    
    @pytest.mark.asyncio
    async def test_categorize_device_phone(self):
        """Test device categorization - phone"""
        scanner = NetworkScanner()
        
        device = {
            'ip': '192.168.1.10',
            'vendor': 'Apple, Inc.',
            'hostname': 'iPhone-User',
            'mac': '11:22:33:44:55:66'
        }
        
        category = await scanner.categorize_device(device)
        assert category == 'phone'
    
    @pytest.mark.asyncio
    async def test_categorize_device_iot(self):
        """Test device categorization - IoT"""
        scanner = NetworkScanner()
        
        device = {
            'ip': '192.168.1.20',
            'vendor': 'Amazon Technologies',
            'hostname': 'echo-living',
            'mac': 'AA:11:BB:22:CC:33'
        }
        
        category = await scanner.categorize_device(device)
        assert category == 'iot'
    
    @pytest.mark.asyncio
    async def test_categorize_device_unknown(self):
        """Test device categorization - unknown"""
        scanner = NetworkScanner()
        
        device = {
            'ip': '192.168.1.99',
            'vendor': 'Unknown',
            'hostname': None,
            'mac': 'FF:FF:FF:FF:FF:FF'
        }
        
        category = await scanner.categorize_device(device)
        assert category == 'unknown'
    
    @pytest.mark.asyncio
    async def test_save_scan_results(self, db_session, mock_arp_scan_result, mock_network_info):
        """Test saving scan results to database"""
        scanner = NetworkScanner()
        scanner.gateway = '192.168.1.1'
        scanner.my_ip = '192.168.1.100'
        
        with patch.object(scanner, 'get_network_info', return_value=mock_network_info):
            scan = await scanner.save_scan_results(
                db=db_session,
                devices=mock_arp_scan_result,
                scan_duration=2.5
            )
        
        assert scan.id is not None
        assert scan.ssid == 'TestNetwork'
        assert scan.gateway == '192.168.1.1'
        assert scan.devices_found == 3
        assert scan.scan_duration == 2.5
    
    @pytest.mark.asyncio
    async def test_full_scan(self, db_session, mock_arp_scan_result, mock_network_info):
        """Test complete scan workflow"""
        scanner = NetworkScanner()
        
        with patch.object(scanner, 'get_network_info', return_value=mock_network_info):
            with patch.object(scanner, 'scan_arp', return_value=mock_arp_scan_result):
                result = await scanner.full_scan(db_session)
        
        assert result['scan_id'] is not None
        assert result['devices_found'] == 3
        assert result['network']['gateway'] == '192.168.1.1'
        assert 'duration' in result
        assert 'timestamp' in result
