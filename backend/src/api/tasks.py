"""
API endpoints for background tasks
Author: Héctor Alejandro Pérez (@halexespejo-cmd)
"""
from fastapi import APIRouter, HTTPException
from src.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/tasks", tags=["Background Tasks"])

# Celery task import (graceful degradation if Celery not available)
try:
    from src.tasks.network import scan_network_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery not available - background tasks disabled")


@router.post("/scan")
async def trigger_background_scan():
    """
    Ejecuta un escaneo de red en background (Celery)
    
    Returns:
        Task ID para seguimiento
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Background tasks not available (Celery not running)"
        )
    
    try:
        task = scan_network_task.apply_async()
        
        logger.info("background_scan_triggered", task_id=task.id)
        
        return {
            "ok": True,
            "task_id": task.id,
            "status": "pending",
            "message": "Network scan started in background"
        }
    
    except Exception as e:
        logger.error("failed_to_trigger_scan", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Obtiene el estado de una tarea en background
    
    Args:
        task_id: ID de la tarea (de /tasks/scan)
    
    Returns:
        Estado de la tarea
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Background tasks not available"
        )
    
    try:
        from celery.result import AsyncResult
        
        task = AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": task.status,  # PENDING, STARTED, SUCCESS, FAILURE, RETRY
            "ready": task.ready()
        }
        
        if task.successful():
            response["result"] = task.result
        elif task.failed():
            response["error"] = str(task.info)
        
        return response
    
    except Exception as e:
        logger.error("failed_to_get_task_status", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
