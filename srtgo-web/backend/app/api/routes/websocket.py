import json
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.services.websocket import connection_manager
from app.services.auth import get_current_user_from_token

router = APIRouter()


@router.websocket("/reservation/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time reservation updates"""
    try:
        await connection_manager.connect(websocket, user_id)
        
        # Send initial connection confirmation
        await connection_manager.send_personal_message(
            {
                "type": "connection_status", 
                "status": "connected",
                "message": "WebSocket 연결 성공"
            },
            user_id
        )
        
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle ping/pong for connection health
            if message.get("type") == "ping":
                await connection_manager.send_personal_message(
                    {"type": "pong", "message": "Connection alive"}, 
                    user_id
                )
                
    except WebSocketDisconnect:
        connection_manager.disconnect(user_id)
        print(f"WebSocket client {user_id} disconnected")
    except Exception as e:
        print(f"WebSocket error for user {user_id}: {e}")
        connection_manager.disconnect(user_id)


@router.get("/connections")
async def get_active_connections():
    """Get number of active WebSocket connections (for debugging)"""
    return {"active_connections": len(connection_manager.active_connections)}