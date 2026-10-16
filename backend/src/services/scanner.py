"""
NetworkScanner - Escaneo ARP y detección de dispositivos
Author: Héctor Alejandro Pérez (@halexespejo-cmd)
"""
import asyncio
import logging
import socket
import struct
from typing import List, Dict, Optional
from datetime import datetime
import subprocess
import re

from scapy.all import ARP, Ether, srp, conf
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.database import Device, NetworkScan
from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Silenciar warnings de scapy
conf.verb = 0


class NetworkScanner:
    """Escanea la red local usando ARP y nmap"""
    
    def __init__(self):
        self.settings = get_settings()
        self.gateway = None
        self.my_ip = None
        self.network_range = None
        
    async def get_network_info(self) -> Dict[str, Optional[str]]:
        """
        Obtiene información de la red actual
        
        Returns:
            dict: gateway, my_ip, ssid, network_range
        """
        try:
            # Obtener IP local y gateway
            info = await asyncio.to_thread(self._get_network_info_sync)
            
            # Calcular rango de red (e.g., 192.168.1.0/24)
            if info['my_ip']:
                octets = info['my_ip'].split('.')
                if len(octets) == 4:
                    info['network_range'] = f"{'.'.join(octets[:3])}.0/24"
            
            self.gateway = info['gateway']
            self.my_ip = info['my_ip']
            self.network_range = info['network_range']
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting network info: {e}")
            return {
                'gateway': None,
                'my_ip': None,
                'ssid': None,
                'network_range': None,
                'public_ip': None
            }
    
    def _get_network_info_sync(self) -> Dict[str, Optional[str]]:
        """Obtiene info de red (sincrónico para threading)"""
        info = {
            'gateway': None,
            'my_ip': None,
            'ssid': None,
            'network_range': None,
            'public_ip': None
        }
        
        try:
            # Gateway default
            with open('/proc/net/route') as f:
                for line in f:
                    fields = line.strip().split()
                    if fields[1] == '00000000':  # Default route
                        gateway_hex = fields[2]
                        # Convertir hex a IP
                        gateway_int = int(gateway_hex, 16)
                        info['gateway'] = socket.inet_ntoa(struct.pack("<L", gateway_int))
                        break
            
            # IP local
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            info['my_ip'] = s.getsockname()[0]
            s.close()
            
            # SSID (intentar con iwgetid)
            try:
                result = subprocess.run(
                    ['iwgetid', '-r'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    info['ssid'] = result.stdout.strip()
            except:
                pass
            
        except Exception as e:
            logger.warning(f"Error getting network info details: {e}")
        
        return info
    
    async def scan_arp(self, target: str = None) -> List[Dict]:
        """
        Escaneo ARP de la red local
        
        Args:
            target: Rango IP (e.g., "192.168.1.0/24"). Si None, usa auto-detect.
        
        Returns:
            Lista de dispositivos encontrados
        """
        if target is None:
            net_info = await self.get_network_info()
            target = net_info.get('network_range', '192.168.1.0/24')
        
        logger.info(f"Starting ARP scan on {target}")
        
        try:
            devices = await asyncio.to_thread(self._arp_scan_sync, target)
            logger.info(f"ARP scan completed: {len(devices)} devices found")
            return devices
        except Exception as e:
            logger.error(f"ARP scan failed: {e}")
            return []
    
    def _arp_scan_sync(self, target: str) -> List[Dict]:
        """Escaneo ARP sincrónico (para threading)"""
        devices = []
        
        try:
            # Crear paquete ARP
            arp = ARP(pdst=target)
            ether = Ether(dst="ff:ff:ff:ff:ff:ff")
            packet = ether / arp
            
            # Enviar y recibir
            result = srp(packet, timeout=3, verbose=0)[0]
            
            for sent, received in result:
                device = {
                    'ip': received.psrc,
                    'mac': received.hwsrc.upper(),
                    'vendor': self._get_vendor(received.hwsrc),
                    'hostname': self._get_hostname(received.psrc),
                    'scan_method': 'arp'
                }
                devices.append(device)
        
        except Exception as e:
            logger.error(f"ARP scan error: {e}")
        
        return devices
    
    def _get_vendor(self, mac: str) -> Optional[str]:
        """
        Obtiene el vendor del MAC address
        
        Args:
            mac: MAC address (e.g., "AA:BB:CC:DD:EE:FF")
        
        Returns:
            Vendor name o None
        """
        # TODO: Integrar con MAC vendors API o base local
        # Por ahora, retornar OUI básico
        oui_prefix = mac.upper().replace(':', '')[:6]
        
        # OUIs comunes (hardcoded básico)
        common_ouis = {
            '001122': 'CISCO SYSTEMS',
            'C4EBFF': 'ZTE Corporation',
            '28107B': 'Amazon Technologies',
            'ACDE48': 'Espressif (ESP32)',
            'B827EB': 'Raspberry Pi Foundation',
            '001DC0': 'Google, Inc.',
            '64D954': 'Apple, Inc.',
            'F45C89': 'Amazon Technologies',
        }
        
        return common_ouis.get(oui_prefix, 'Unknown Vendor')
    
    def _get_hostname(self, ip: str) -> Optional[str]:
        """
        Obtiene el hostname de una IP
        
        Args:
            ip: IP address
        
        Returns:
            Hostname o None
        """
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except:
            return None
    
    async def categorize_device(self, device: Dict) -> str:
        """
        Categoriza un dispositivo según vendor, hostname, MAC
        
        Args:
            device: Diccionario con info del dispositivo
        
        Returns:
            Categoría: router, tv, phone, laptop, camera, iot, unknown
        """
        vendor = (device.get('vendor') or '').lower()
        hostname = (device.get('hostname') or '').lower()
        mac = device.get('mac', '')
        
        # Router
        if device.get('ip') == self.gateway:
            return 'router'
        
        if any(k in vendor for k in ['cisco', 'zte', 'huawei', 'tp-link', 'netgear']):
            return 'router'
        
        # TV / Streaming
        if any(k in vendor + hostname for k in ['samsung', 'lg', 'sony', 'roku', 'chromecast', 'fire']):
            return 'tv'
        
        # Phones
        if any(k in vendor + hostname for k in ['apple', 'iphone', 'samsung', 'xiaomi', 'huawei', 'android']):
            return 'phone'
        
        # Laptops
        if any(k in vendor + hostname for k in ['dell', 'hp', 'lenovo', 'asus', 'acer', 'macbook']):
            return 'laptop'
        
        # Cameras
        if any(k in vendor + hostname for k in ['camera', 'hikvision', 'dahua', 'axis']):
            return 'camera'
        
        # IoT / Smart Home
        if any(k in vendor + hostname for k in ['espressif', 'esp32', 'esp8266', 'amazon', 'alexa', 'echo', 'google home']):
            return 'iot'
        
        return 'unknown'
    
    async def save_scan_results(
        self, 
        db: AsyncSession,
        devices: List[Dict],
        scan_duration: float
    ) -> NetworkScan:
        """
        Guarda los resultados del escaneo en la DB
        
        Args:
            db: Sesión de base de datos
            devices: Lista de dispositivos encontrados
            scan_duration: Duración del escaneo en segundos
        
        Returns:
            NetworkScan creado
        """
        net_info = await self.get_network_info()
        
        # Crear registro de escaneo
        scan = NetworkScan(
            ssid=net_info.get('ssid'),
            gateway=net_info.get('gateway'),
            my_ip=net_info.get('my_ip'),
            public_ip=net_info.get('public_ip'),
            devices_found=len(devices),
            scan_duration=scan_duration,
            scanned_at=datetime.utcnow(),
            scan_type='arp'
        )
        
        db.add(scan)
        
        # Actualizar o crear dispositivos
        for device_data in devices:
            mac = device_data['mac']
            
            # Buscar dispositivo existente
            result = await db.execute(
                select(Device).where(Device.mac == mac)
            )
            device = result.scalar_one_or_none()
            
            if device:
                # Actualizar existente
                device.ip = device_data['ip']
                device.vendor = device_data.get('vendor')
                device.hostname = device_data.get('hostname')
                device.last_seen = datetime.utcnow()
                
                # Determinar si es router
                if device_data['ip'] == self.gateway:
                    device.is_self = True
                
            else:
                # Crear nuevo
                category = await self.categorize_device(device_data)
                
                device = Device(
                    mac=mac,
                    ip=device_data['ip'],
                    vendor=device_data.get('vendor'),
                    hostname=device_data.get('hostname'),
                    category=category,
                    is_blocked=False,
                    is_self=(device_data['ip'] == self.gateway or device_data['ip'] == self.my_ip),
                    first_seen=datetime.utcnow(),
                    last_seen=datetime.utcnow()
                )
                db.add(device)
        
        await db.commit()
        await db.refresh(scan)
        
        return scan
    
    async def full_scan(self, db: AsyncSession) -> Dict:
        """
        Escaneo completo: ARP + guardar resultados
        
        Args:
            db: Sesión de base de datos
        
        Returns:
            Resumen del escaneo
        """
        start_time = datetime.utcnow()
        
        # Obtener info de red
        net_info = await self.get_network_info()
        
        # Escaneo ARP
        devices = await self.scan_arp()
        
        # Duración
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Guardar
        scan = await self.save_scan_results(db, devices, duration)
        
        return {
            'scan_id': scan.id,
            'network': net_info,
            'devices_found': len(devices),
            'duration': duration,
            'timestamp': scan.scanned_at.isoformat()
        }
