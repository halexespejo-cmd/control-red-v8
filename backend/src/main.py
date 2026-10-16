"""
FastAPI application - Control de Red Backend v9
"""
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.config import get_settings
from src.models.database import init_db, get_db
from src.api.devices import router as devices_router
from src.api.auth import router as auth_router
from src.api.tasks import router as tasks_router
from src.utils.logging import configure_logging, get_logger
from src.utils.cache import get_redis, close_redis
from prometheus_fastapi_instrumentator import Instrumentator

# Configure structured logging
settings_pre = get_settings()
configure_logging(
    log_level=settings_pre.LOG_LEVEL,
    json_logs=not settings_pre.DEBUG  # JSON in production, console in dev
)

logger = get_logger(__name__)

settings = get_settings()

# Initialize Sentry (optional, configure with SENTRY_DSN env var)
if hasattr(settings, 'SENTRY_DSN') and settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,  # 10% performance monitoring
        environment=settings.APP_NAME,
        release=settings.VERSION,
    )
    logger.info("✅ Sentry initialized")

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eventos de ciclo de vida de la aplicación"""
    # Startup
    logger.info("🚀 Starting %s v%s", settings.APP_NAME, settings.VERSION)
    logger.info("📊 Debug mode: %s", settings.DEBUG)
    
    # Inicializar base de datos
    await init_db()
    logger.info("✅ Database initialized")
    
    # Initialize Redis
    redis_client = await get_redis()
    if redis_client:
        logger.info("✅ Redis cache initialized")
    else:
        logger.warning("⚠️  Redis unavailable - cache disabled")
    
    # Inicializar ARP Blocker
    from src.services.arp_blocker import get_arp_blocker
    from src.services.scanner import NetworkScanner
    
    try:
        scanner = NetworkScanner()
        net_info = await scanner.get_network_info()
        
        if net_info.get('gateway'):
            blocker = get_arp_blocker()
            await blocker.initialize(
                gateway_ip=net_info['gateway']
            )
            logger.info("✅ ARP Blocker initialized (requires sudo for real blocking)")
        else:
            logger.warning("⚠️  No gateway detected, ARP Blocker not initialized")
    except Exception as e:
        logger.warning(f"⚠️  ARP Blocker initialization failed: {e} (run with sudo for real blocking)")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down %s", settings.APP_NAME)
    
    # Detener todos los bloqueos
    try:
        from src.services.arp_blocker import get_arp_blocker
        blocker = get_arp_blocker()
        if blocker.is_initialized:
            await blocker.stop_all()
            logger.info("✅ All ARP blocks stopped")
    except Exception as e:
        logger.warning(f"⚠️  Error stopping ARP blocks: {e}")
    
    # Close Redis
    await close_redis()
    logger.info("✅ Redis connection closed")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Backend modular para control de red vía ARP",
    lifespan=lifespan
)

# Rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(auth_router)
app.include_router(devices_router)
app.include_router(tasks_router)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)


@app.get("/", tags=["Health"])
@limiter.limit("100/minute")
async def root(request: Request):
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
@limiter.limit("50/minute")
async def get_status(request: Request, db: AsyncSession = Depends(get_db)):
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
        
        # Estado del blocker
        from src.services.arp_blocker import get_arp_blocker
        blocker = get_arp_blocker()
        
        enforcement = "none"
        enforcement_note = "Scanner activo"
        
        if blocker.is_initialized:
            active_blocks = blocker.get_blocked_devices()
            if len(active_blocks) > 0:
                enforcement = "arp_active"
                enforcement_note = f"ARP spoofing active: {len(active_blocks)} device(s) blocked"
            else:
                enforcement = "ready"
                enforcement_note = "ARP Blocker ready (no active blocks)"
        else:
            enforcement = "simulate"
            enforcement_note = "ARP Blocker not initialized (run with sudo for real blocking)"
        
        return {
            "ok": True,
            "driver": "host_lan",
            "enforcement": enforcement,
            "enforcement_note": enforcement_note,
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
