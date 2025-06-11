import json
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.services.websocket import ConnectionManager
from app.services.auth import get_current_user_from_token

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/reservation/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time reservation updates"""
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle ping/pong for connection health
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)


@router.get("/connections")
async def get_active_connections():
    """Get number of active WebSocket connections (for debugging)"""
    return {"active_connections": len(manager.active_connections)}