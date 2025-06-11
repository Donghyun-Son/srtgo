from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.database import get_session
from app.models import User, UserSettings, UserSettingsCreate, UserSettingsRead, UserSettingsUpdate
from app.services.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[UserSettingsRead])
def get_user_settings(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all settings for current user"""
    statement = select(UserSettings).where(UserSettings.user_id == current_user.id)
    settings = session.exec(statement).all()
    return settings


@router.get("/{rail_type}", response_model=UserSettingsRead)
def get_user_settings_by_rail_type(
    rail_type: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get settings for specific rail type"""
    statement = select(UserSettings).where(
        UserSettings.user_id == current_user.id,
        UserSettings.rail_type == rail_type
    )
    settings = session.exec(statement).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings


@router.post("/", response_model=UserSettingsRead)
def create_user_settings(
    settings: UserSettingsCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create new user settings"""
    settings.user_id = current_user.id
    db_settings = UserSettings.model_validate(settings)
    session.add(db_settings)
    session.commit()
    session.refresh(db_settings)
    return db_settings


@router.put("/{settings_id}", response_model=UserSettingsRead)
def update_user_settings(
    settings_id: int,
    settings_update: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update user settings"""
    statement = select(UserSettings).where(
        UserSettings.id == settings_id,
        UserSettings.user_id == current_user.id
    )
    db_settings = session.exec(statement).first()
    if not db_settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    settings_data = settings_update.model_dump(exclude_unset=True)
    for key, value in settings_data.items():
        setattr(db_settings, key, value)
    
    session.add(db_settings)
    session.commit()
    session.refresh(db_settings)
    return db_settings


@router.delete("/{settings_id}")
def delete_user_settings(
    settings_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete user settings"""
    statement = select(UserSettings).where(
        UserSettings.id == settings_id,
        UserSettings.user_id == current_user.id
    )
    db_settings = session.exec(statement).first()
    if not db_settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    session.delete(db_settings)
    session.commit()
    return {"message": "Settings deleted successfully"}