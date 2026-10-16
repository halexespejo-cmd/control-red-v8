"""
SQLAlchemy models para persistencia
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import AsyncGenerator

from src.config import get_settings

Base = declarative_base()
settings = get_settings()


class Device(Base):
    """Dispositivo en la red"""
    __tablename__ = 'devices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    mac = Column(String(17), unique=True, index=True, nullable=False)
    ip = Column(String(15))
    vendor = Column(String(100))
    hostname = Column(String(100))
    custom_name = Column(String(50))
    
    # Categorización
    category = Column(String(20))  # router, tv, phone, laptop, camera, iot, unknown
    device_type = Column(String(50))
    
    # Estado
    is_blocked = Column(Boolean, default=False)
    is_self = Column(Boolean, default=False)
    random_mac = Column(Boolean, default=False)
    
    # Timestamps
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    blocked_at = Column(DateTime, nullable=True)
    
    # Metadata adicional
    metadata_json = Column(JSON, nullable=True)


class Schedule(Base):
    """Horario programado de bloqueo"""
    __tablename__ = 'schedules'
    
    id = Column(String(36), primary_key=True)  # UUID
    mac = Column(String(17), index=True, nullable=False)
    
    # Horario
    start_time = Column(String(5), nullable=False)  # HH:MM
    end_time = Column(String(5), nullable=False)
    
    # Días de la semana (0-6, lunes-domingo)
    days_of_week = Column(String(20), default="0,1,2,3,4,5,6")
    
    # Estado
    enabled = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    """Log de auditoría de acciones"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Acción
    action = Column(String(20), nullable=False)  # BLOCK, UNBLOCK, SCAN
    target_mac = Column(String(17))
    target_ip = Column(String(15))
    
    # Usuario (Telegram)
    user_id = Column(String(50))
    username = Column(String(100))
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Metadata adicional
    metadata_json = Column(JSON, nullable=True)
    
    # Resultado
    success = Column(Boolean, default=True)
    error_message = Column(String(500))


class NetworkScan(Base):
    """Registro de escaneos de red"""
    __tablename__ = 'network_scans'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Info de la red
    ssid = Column(String(100))
    gateway = Column(String(15))
    my_ip = Column(String(15))
    public_ip = Column(String(15))
    
    # Resultados
    devices_found = Column(Integer)
    scan_duration = Column(Float)  # segundos
    
    # Timestamp
    scanned_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Metadata
    scan_type = Column(String(20))  # 'arp', 'nmap', 'full'
    metadata_json = Column(JSON)


# Database engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_size=settings.DATABASE_POOL_SIZE if 'postgresql' in settings.DATABASE_URL else 5,
    max_overflow=settings.DATABASE_MAX_OVERFLOW if 'postgresql' in settings.DATABASE_URL else 10,
    pool_pre_ping=True,  # Verify connections before use
)

# Session factory
async_session_maker = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


async def init_db():
    """Crear todas las tablas"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para obtener sesión de DB
    
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
