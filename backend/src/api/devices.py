"""
API Endpoints - Devices
Author: Héctor Alejandro Pérez (@halexespejo-cmd)
"""
import logging
from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.models.database import get_db, Device
from src.models.device import (
    DeviceResponse,
    DevicesListResponse,
    DeviceUpdate
)
from src.services.scanner import NetworkScanner

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/devices", tags=["Devices"])


@router.get("/", response_model=DevicesListResponse)
async def get_devices(
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
        
        return DevicesListResponse(
            devices=[DeviceResponse.model_validate(d) for d in devices],
            total=len(devices),
            blocked_count=blocked_count
        )
    
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
    Bloquea un dispositivo (marca como bloqueado)
    
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
        
        device.is_blocked = True
        device.blocked_at = datetime.utcnow()
        
        await db.commit()
        
        # TODO: Aquí iría la lógica real de ARP spoofing (Sesión 3)
        logger.info(f"Device {mac} marked as blocked (ARP enforcement pending)")
        
        return {
            "ok": True,
            "mac": mac,
            "is_blocked": True,
            "message": "Device marked as blocked (enforcement will be added in Session 3)"
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
        
        device.is_blocked = False
        device.blocked_at = None
        
        await db.commit()
        
        logger.info(f"Device {mac} unblocked")
        
        return {
            "ok": True,
            "mac": mac,
            "is_blocked": False,
            "message": "Device unblocked"
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
        scanner = NetworkScanner()
        result = await scanner.full_scan(db)
        
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
