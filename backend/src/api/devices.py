"""
API Endpoints - Devices
Author: Héctor Alejandro Pérez (@halexespejo-cmd)
"""
import logging
from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, func

from src.models.database import get_db, Device
from src.models.device import (
    DeviceResponse,
    DevicesListResponse,
    DeviceUpdate
)
from src.services.scanner import NetworkScanner
from src.services.arp_blocker import get_arp_blocker
from src.utils.cache import get_cache, set_cache, delete_pattern
from src.utils.cache_decorator import cache_endpoint
from src.utils.websocket import broadcast_device_event, broadcast_scan_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/devices", tags=["Devices"])

# Celery task import (optional - graceful degradation if Celery not available)
try:
    from src.tasks.network import scan_network_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery not available - background tasks disabled")


@router.get("/", response_model=DevicesListResponse)
@cache_endpoint(ttl=60, key_prefix="devices_list")
async def get_devices(
    request: Request,
    blocked_only: bool = Query(False, description="Solo dispositivos bloqueados"),
    category: str = Query(None, description="Filtrar por categoría"),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todos los dispositivos en la base de datos
    
    Args:
        blocked_only: Si True, solo bloqueados
        category: Filtrar por categoría (router, tv, phone, etc.)
        db: Sesión de base de datos
    
    Returns:
        Lista de dispositivos
    """
    try:
        # Try cache first
        cache_key = f"devices:list:blocked={blocked_only}:category={category}"
        cached = await get_cache(cache_key)
        if cached:
            return cached
        
        # Construir query
        query = select(Device)
        
        if blocked_only:
            query = query.where(Device.is_blocked == True)
        
        if category:
            query = query.where(Device.category == category)
        
        # Ejecutar
        result = await db.execute(query)
        devices = result.scalars().all()
        
        # Contar bloqueados
        blocked_count = sum(1 for d in devices if d.is_blocked)
        
        response = DevicesListResponse(
            devices=[DeviceResponse.model_validate(d) for d in devices],
            total=len(devices),
            blocked_count=blocked_count
        )
        
        # Cache for 30 seconds
        await set_cache(cache_key, response.model_dump(), ttl=30)
        
        return response
    
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{mac}", response_model=DeviceResponse)
async def get_device(
    mac: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene un dispositivo por MAC address
    
    Args:
        mac: MAC address (con : o -)
        db: Sesión de base de datos
    
    Returns:
        Dispositivo encontrado
    """
    try:
        # Normalizar MAC
        mac_normalized = mac.upper().replace('-', ':')
        
        result = await db.execute(
            select(Device).where(Device.mac == mac_normalized)
        )
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        return DeviceResponse.model_validate(device)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device {mac}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{mac}", response_model=DeviceResponse)
async def update_device(
    mac: str,
    device_update: DeviceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza un dispositivo (nombre, categoría, etc.)
    
    Args:
        mac: MAC address
        device_update: Datos a actualizar
        db: Sesión de base de datos
    
    Returns:
        Dispositivo actualizado
    """
    try:
        # Normalizar MAC
        mac_normalized = mac.upper().replace('-', ':')
        
        result = await db.execute(
            select(Device).where(Device.mac == mac_normalized)
        )
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Actualizar campos
        update_data = device_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(device, field, value)
        
        await db.commit()
        await db.refresh(device)
        
        # Invalidate cache
        await delete_pattern("devices:*")
        
        return DeviceResponse.model_validate(device)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating device {mac}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{mac}/block")
async def block_device(
    mac: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Bloquea un dispositivo vía ARP spoofing
    
    Args:
        mac: MAC address
        db: Sesión de base de datos
    
    Returns:
        Estado de la operación
    """
    try:
        mac_normalized = mac.upper().replace('-', ':')
        
        result = await db.execute(
            select(Device).where(Device.mac == mac_normalized)
        )
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        if device.is_self:
            raise HTTPException(
                status_code=400, 
                detail="Cannot block self or router"
            )
        
        if device.is_blocked:
            return {
                "ok": True,
                "mac": mac,
                "is_blocked": True,
                "message": "Device already blocked"
            }
        
        # Marcar en DB
        device.is_blocked = True
        device.blocked_at = datetime.utcnow()
        await db.commit()
        
        # ARP spoofing real
        blocker = get_arp_blocker()
        
        if blocker.is_initialized:
            success = await blocker.block_device(device.ip, device.mac)
            
            if success:
                logger.info(f"Device {mac} blocked via ARP spoofing")
                return {
                    "ok": True,
                    "mac": mac,
                    "is_blocked": True,
                    "enforcement": "arp_active",
                    "message": "Device blocked successfully"
                }
            else:
                logger.error(f"ARP blocking failed for {mac}")
                return {
                    "ok": False,
                    "mac": mac,
                    "is_blocked": True,
                    "enforcement": "db_only",
                    "message": "Marked as blocked in DB, but ARP enforcement failed"
                }
        else:
            logger.warning("ARPBlocker not initialized, DB-only block")
            return {
                "ok": True,
                "mac": mac,
                "is_blocked": True,
                "enforcement": "db_only",
                "message": "Device marked as blocked (ARP blocker not initialized - run with sudo)"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error blocking device {mac}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{mac}/unblock")
async def unblock_device(
    mac: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Desbloquea un dispositivo
    
    Args:
        mac: MAC address
        db: Sesión de base de datos
    
    Returns:
        Estado de la operación
    """
    try:
        mac_normalized = mac.upper().replace('-', ':')
        
        result = await db.execute(
            select(Device).where(Device.mac == mac_normalized)
        )
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Detener ARP spoofing
        blocker = get_arp_blocker()
        if blocker.is_initialized and device.is_blocked:
            await blocker.unblock_device(device.mac)
        
        # Actualizar DB
        device.is_blocked = False
        device.blocked_at = None
        
        await db.commit()
        
        logger.info(f"Device {mac} unblocked")
        
        return {
            "ok": True,
            "mac": mac,
            "is_blocked": False,
            "message": "Device unblocked successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unblocking device {mac}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan")
async def trigger_scan(
    db: AsyncSession = Depends(get_db)
):
    """
    Ejecuta un escaneo de red manual
    
    Args:
        db: Sesión de base de datos
    
    Returns:
        Resultado del escaneo
    """
    try:
        # Broadcast scan start
        await broadcast_scan_event("scan_started", {"message": "Network scan initiated"})
        
        scanner = NetworkScanner()
        result = await scanner.full_scan(db)
        
        # Broadcast scan complete
        await broadcast_scan_event("scan_completed", {
            "devices_found": result.get('devices_found', 0),
            "scan_id": result.get('scan_id')
        })
        
        return {
            "ok": True,
            "scan_id": result['scan_id'],
            "devices_found": result['devices_found'],
            "duration": result['duration'],
            "network": result['network'],
            "timestamp": result['timestamp']
        }
    
    except Exception as e:
        logger.error(f"Error during scan: {e}")
        await broadcast_scan_event("scan_failed", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network/info")
async def get_network_info():
    """
    Información de la red actual (sin escaneo)
    
    Returns:
        Info de red: gateway, IP, SSID
    """
    try:
        scanner = NetworkScanner()
        info = await scanner.get_network_info()
        
        return {
            "ok": True,
            **info
        }
    
    except Exception as e:
        logger.error(f"Error getting network info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/blocked/active")
async def get_active_blocks():
    """
    Lista de dispositivos con bloqueo ARP activo
    
    Returns:
        Dispositivos con ARP spoofing activo
    """
    try:
        blocker = get_arp_blocker()
        
        if not blocker.is_initialized:
            return {
                "ok": False,
                "message": "ARP Blocker not initialized",
                "active_blocks": {}
            }
        
        active_blocks = blocker.get_blocked_devices()
        
        return {
            "ok": True,
            "count": len(active_blocks),
            "active_blocks": active_blocks
        }
    
    except Exception as e:
        logger.error(f"Error getting active blocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
