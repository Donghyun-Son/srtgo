"""API routes."""
from .auth import router as auth_router
from .credentials import router as credentials_router
from .reservations import router as reservations_router
from .trains import router as trains_router

__all__ = [
    "auth_router",
    "credentials_router",
    "reservations_router",
    "trains_router",
]
