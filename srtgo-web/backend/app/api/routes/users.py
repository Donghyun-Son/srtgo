from fastapi import APIRouter, Depends
from app.models import User, UserRead
from app.services.auth import get_current_user

router = APIRouter()


@router.get("/me", response_model=UserRead)
def read_user_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user