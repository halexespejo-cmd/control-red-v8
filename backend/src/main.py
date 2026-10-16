"""
FastAPI application - Control de Red Backend v9
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.config import get_settings
from src.models.database import init_db, get_db
from src.api.devices import router as devices_router

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eventos de ciclo de vida de la aplicación"""
    # Startup
    logger.info("🚀 Starting %s v%s", settings.APP_NAME, settings.VERSION)
    logger.info("📊 Debug mode: %s", settings.DEBUG)
    
    # Inicializar base de datos
    await init_db()
    logger.info("✅ Database initialized")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down %s", settings.APP_NAME)


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Backend modular para control de red vía ARP",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(devices_router)


@app.get("/", tags=["Health"])
async def root():
    """
    Health check endpoint
    
    Returns:
        dict: Estado de la aplicación
    """
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running",
        "debug": settings.DEBUG
    }


@app.get("/api/status", tags=["Status"])
async def get_status(db: AsyncSession = Depends(get_db)):
    """
    Estado general del sistema
    
    Returns:
        dict: Estado actual del backend
    """
    from sqlalchemy import select, func
    from src.models.database import Device
    from src.services.scanner import NetworkScanner
    
    try:
        # Contar dispositivos
        result = await db.execute(select(func.count(Device.id)))
        total_devices = result.scalar_one()
        
        result = await db.execute(
            select(func.count(Device.id)).where(Device.is_blocked == True)
        )
        blocked_devices = result.scalar_one()
        
        # Info de red
        scanner = NetworkScanner()
        net_info = await scanner.get_network_info()
        
        return {
            "ok": True,
            "driver": "host_lan",
            "enforcement": "simulate",
            "enforcement_note": "Scanner activo - ARP blocker pending (Sesión 3)",
            "network": {
                "ssid": net_info.get('ssid'),
                "gateway": net_info.get('gateway'),
                "my_ip": net_info.get('my_ip'),
                "public_ip": net_info.get('public_ip')
            },
            "devices_total": total_devices,
            "devices_paused": blocked_devices,
            "ui": settings.VERSION
        }
    
    except Exception as e:
        logger.error(f"Error in status endpoint: {e}")
        return {
            "ok": False,
            "error": str(e),
            "driver": "host_lan",
            "enforcement": "error"
        }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """Manejador global de excepciones"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "error": str(exc),
            "detail": "Internal server error"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
