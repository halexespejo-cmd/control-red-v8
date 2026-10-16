"""
WebSocket Connection Manager for Real-time Updates
Author: Héctor Alejandro Pérez (@halexespejo-cmd)
"""
import asyncio
import json
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections and broadcast messages"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str = None):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(websocket)
        
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket, user_id: str = None):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if user_id and user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connections"""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_to_user(self, user_id: str, message: dict):
        """Broadcast message to specific user's connections"""
        if user_id not in self.user_connections:
            return
        
        disconnected = []
        
        for connection in self.user_connections[user_id]:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                logger.error(f"Error broadcasting to user: {e}")
                disconnected.append(connection)
        
        # Clean up
        for conn in disconnected:
            self.disconnect(conn, user_id)
    
    async def heartbeat(self, websocket: WebSocket, interval: int = 30):
        """Send periodic heartbeat to keep connection alive"""
        try:
            while True:
                await asyncio.sleep(interval)
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                })
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")


# Global connection manager
manager = ConnectionManager()


async def broadcast_device_event(event_type: str, device_data: dict):
    """
    Broadcast device-related events to all clients
    
    Args:
        event_type: 'device_discovered', 'device_blocked', 'device_unblocked', 'device_updated'
        device_data: Device information dict
    """
    message = {
        "type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": device_data
    }
    await manager.broadcast(message)


async def broadcast_scan_event(status: str, data: dict = None):
    """
    Broadcast network scan events
    
    Args:
        status: 'scan_started', 'scan_progress', 'scan_completed', 'scan_failed'
        data: Optional scan data (devices found, progress %, error message)
    """
    message = {
        "type": "scan_event",
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data or {}
    }
    await manager.broadcast(message)


async def broadcast_system_event(event_type: str, message_text: str):
    """
    Broadcast system events
    
    Args:
        event_type: 'system_info', 'system_warning', 'system_error'
        message_text: Event message
    """
    message = {
        "type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "message": message_text
    }
    await manager.broadcast(message)
