"""Credential schemas for storing user credentials."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


# Train Credentials
class TrainCredentialCreate(BaseModel):
    """Schema for creating train credentials."""
    train_type: str = Field(..., pattern="^(SRT|KTX)$")
    user_id: str = Field(..., description="Login ID for train service")
    password: str = Field(..., min_length=4)
    preferences: Optional[Dict[str, Any]] = None


class TrainCredentialResponse(BaseModel):
    """Schema for train credential response."""
    id: int
    train_type: str
    # Don't expose encrypted fields
    preferences: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Card Credentials
class CardCredentialCreate(BaseModel):
    """Schema for creating card credentials."""
    card_number: str = Field(..., min_length=15, max_length=16)
    card_password: str = Field(..., min_length=2)
    birthday: str = Field(..., pattern=r"^\d{6}$")  # YYMMDD
    expire: str = Field(..., pattern=r"^\d{4}$")  # YYMM
    card_nickname: Optional[str] = None


class CardCredentialResponse(BaseModel):
    """Schema for card credential response."""
    id: int
    card_last4: Optional[str] = None
    card_nickname: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Telegram Credentials
class TelegramCredentialCreate(BaseModel):
    """Schema for creating Telegram credentials."""
    token: str = Field(..., min_length=10)
    chat_id: str = Field(..., min_length=1)
    is_enabled: bool = True


class TelegramCredentialResponse(BaseModel):
    """Schema for Telegram credential response."""
    id: int
    is_enabled: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
