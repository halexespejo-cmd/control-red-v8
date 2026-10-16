"""
Pydantic models para validación y serialización
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re


class DeviceBase(BaseModel):
    """Modelo base de dispositivo"""
    mac: str = Field(..., description="MAC address (formato: aa:bb:cc:dd:ee:ff)")
    ip: Optional[str] = None
    vendor: Optional[str] = None
    hostname: Optional[str] = None
    custom_name: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = None
    device_type: Optional[str] = None
    
    @field_validator('mac')
    @classmethod
    def validate_mac(cls, v: str) -> str:
        """Validar formato MAC address"""
        pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        if not re.match(pattern, v):
            raise ValueError('Invalid MAC address format. Expected: aa:bb:cc:dd:ee:ff')
        return v.lower()


class DeviceCreate(DeviceBase):
    """Schema para crear dispositivo"""
    pass


class DeviceResponse(DeviceBase):
    """Schema de respuesta de dispositivo"""
    id: int
    is_blocked: bool = False
    is_self: bool = False
    paused: bool = False  # Alias de is_blocked para frontend v8
    first_seen: datetime
    last_seen: datetime
    blocked_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DeviceUpdate(BaseModel):
    """Schema para actualizar dispositivo (campos opcionales)"""
    custom_name: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = None
    device_type: Optional[str] = None


class DeviceListResponse(BaseModel):
    """Respuesta de lista de dispositivos"""
    ok: bool = True
    devices: List[DeviceResponse]
    total: int
    last_scan: Optional[datetime] = None
    scanning: bool = False


class DevicesListResponse(BaseModel):
    """Respuesta de lista de dispositivos (alias para API)"""
    devices: List[DeviceResponse]
    total: int
    blocked_count: int


class ScheduleBase(BaseModel):
    """Modelo base de horario"""
    mac: str = Field(..., pattern=r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    start: str = Field(..., pattern=r'^\d{2}:\d{2}$', description="Hora inicio (HH:MM)")
    end: str = Field(..., pattern=r'^\d{2}:\d{2}$', description="Hora fin (HH:MM)")
    days_of_week: str = "0,1,2,3,4,5,6"


class ScheduleCreate(ScheduleBase):
    """Schema para crear horario"""
    pass


class ScheduleResponse(ScheduleBase):
    """Schema de respuesta de horario"""
    id: str
    enabled: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class NetworkInfo(BaseModel):
    """Información de la red actual"""
    ssid: Optional[str] = None
    gateway: Optional[str] = None
    my_ip: Optional[str] = None
    public_ip: Optional[str] = None


class StatusResponse(BaseModel):
    """Estado general del sistema"""
    ok: bool = True
    driver: str = "host_lan"
    enforcement: str  # 'arp_block', 'simulate', 'none'
    enforcement_note: str
    network: NetworkInfo
    devices_total: int = 0
    devices_paused: int = 0
    ui: str  # Versión del frontend
