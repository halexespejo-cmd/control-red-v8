"""
WebSocket API Router
Author: Héctor Alejandro Pérez (@halexespejo-cmd)
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from src.utils.websocket import manager
from src.utils.auth import decode_access_token
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates
    
    Connect: ws://localhost:8000/ws
    Optional: ws://localhost:8000/ws?token=<jwt_token>
    """
    # Get token from query params (optional)
    token = websocket.query_params.get("token")
    user_id = None
    
    if token:
        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
        except Exception as e:
            logger.warning(f"Invalid WebSocket token: {e}")
    
    await manager.connect(websocket, user_id)
    
    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "connection_established",
            "message": "Connected to Control de Red WebSocket",
            "user_id": user_id
        }, websocket)
        
        # Keep connection alive and listen for messages
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Handle different message types
            message_type = data.get("type")
            
            if message_type == "ping":
                # Respond to ping
                await manager.send_personal_message({
                    "type": "pong"
                }, websocket)
            
            elif message_type == "subscribe":
                # Client wants to subscribe to specific events
                await manager.send_personal_message({
                    "type": "subscribed",
                    "message": "Subscribed to real-time updates"
                }, websocket)
            
            else:
                # Echo unknown messages
                await manager.send_personal_message({
                    "type": "echo",
                    "data": data
                }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"Client disconnected: {user_id or 'anonymous'}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)
