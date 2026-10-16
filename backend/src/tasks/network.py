"""
Celery tasks for network operations
Author: Héctor Alejandro Pérez (@halexespejo-cmd)
"""
import asyncio
from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession

from src.celery_app import celery_app
from src.services.scanner import NetworkScanner
from src.models.database import async_session_maker
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AsyncTask(Task):
    """
    Base task class for async operations
    Ensures event loop is properly managed
    """
    def __call__(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.run(*args, **kwargs))
    
    async def run(self, *args, **kwargs):
        raise NotImplementedError()


@celery_app.task(bind=True, base=AsyncTask, name="src.tasks.network.scan_network")
async def scan_network_task(self):
    """
    Background task to scan network for devices
    
    Returns:
        Dict with scan results
    """
    try:
        logger.info("celery_task_started", task="scan_network")
        
        scanner = NetworkScanner()
        
        # Get DB session
        async with async_session_maker() as db:
            result = await scanner.scan_network(db)
        
        logger.info("celery_task_completed", 
                   task="scan_network",
                   devices_found=result.get("devices_found", 0))
        
        return {
            "status": "success",
            "devices_found": result.get("devices_found", 0),
            "scan_duration": result.get("scan_duration", 0)
        }
    
    except Exception as e:
        logger.error("celery_task_failed", task="scan_network", error=str(e))
        raise


@celery_app.task(bind=True, base=AsyncTask, name="src.tasks.network.periodic_network_scan")
async def periodic_network_scan(self):
    """
    Periodic task to scan network (scheduled by beat)
    
    Returns:
        Dict with scan results
    """
    try:
        logger.info("periodic_scan_started")
        
        scanner = NetworkScanner()
        
        async with async_session_maker() as db:
            result = await scanner.scan_network(db)
        
        logger.info("periodic_scan_completed", 
                   devices_found=result.get("devices_found", 0))
        
        return {
            "status": "success",
            "devices_found": result.get("devices_found", 0)
        }
    
    except Exception as e:
        logger.error("periodic_scan_failed", error=str(e))
        raise


@celery_app.task(bind=True, name="src.tasks.network.cleanup_old_scans")
def cleanup_old_scans_task(self, days: int = 30):
    """
    Cleanup old network scans from database
    
    Args:
        days: Delete scans older than N days
    
    Returns:
        Number of deleted scans
    """
    try:
        from datetime import datetime, timedelta
        from src.models.database import NetworkScan
        
        logger.info("cleanup_started", days=days)
        
        # This is a simplified sync version
        # For proper async, use AsyncTask base class
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # TODO: Implement actual deletion with async DB
        # For now, just return mock result
        
        logger.info("cleanup_completed", days=days)
        
        return {
            "status": "success",
            "deleted": 0,
            "cutoff_date": cutoff_date.isoformat()
        }
    
    except Exception as e:
        logger.error("cleanup_failed", error=str(e))
        raise
