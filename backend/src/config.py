"""
Configuración de la aplicación
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Configuración global de Control de Red Backend"""
    
    # App
    APP_NAME: str = "Control de Red Backend"
    VERSION: str = "9.0.0-dev.1"
    DEBUG: bool = True
    
    # Network
    NETWORK_INTERFACE: str = "wlan0"  # o "eth0"
    SCAN_INTERVAL: int = 15  # segundos entre escaneos automáticos
    ARP_INTERVAL: int = 2     # segundos entre paquetes ARP durante bloqueo
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./control_red.db"
    # For PostgreSQL use: "postgresql+asyncpg://user:pass@localhost/dbname"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Security
    ALLOWED_ORIGINS: List[str] = [
        "https://halexespejo-cmd.github.io",
        "http://localhost:5173",
        "http://localhost:3000",
        "https://raw.githack.com"
    ]
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Sentry (optional - error tracking)
    SENTRY_DSN: str = ""
    
    # Redis (cache)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Celery (background tasks)
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Singleton de configuración (cacheado)"""
    return Settings()
