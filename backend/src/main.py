"""
FastAPI application - Control de Red Backend v9
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from src.config import get_settings
from src.models.database import init_db

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
async def get_status():
    """
    Estado general del sistema
    
    Returns:
        dict: Estado actual del backend
    """
    return {
        "ok": True,
        "driver": "host_lan",
        "enforcement": "simulate",  # Placeholder - se cambiará cuando blocker esté listo
        "enforcement_note": "Backend inicializado - scanner y blocker pendientes",
        "network": {
            "ssid": None,
            "gateway": None,
            "my_ip": None,
            "public_ip": None
        },
        "devices_total": 0,
        "devices_paused": 0,
        "ui": settings.VERSION
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
