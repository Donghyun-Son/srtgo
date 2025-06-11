from fastapi import APIRouter
from app.api.routes import auth, users, settings, reservations, websocket, utils

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(reservations.router, prefix="/reservations", tags=["reservations"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
api_router.include_router(utils.router, prefix="/utils", tags=["utilities"])