from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, JSON, Column


class UserSettingsBase(SQLModel):
    user_id: int = Field(foreign_key="user.id")
    rail_type: str  # "SRT" or "KTX"
    
    # Login credentials (encrypted)
    login_id: Optional[str] = None
    encrypted_password: Optional[str] = None
    
    # Station preferences
    favorite_stations: list[str] = Field(default=[], sa_column=Column(JSON))
    default_departure: Optional[str] = None
    default_arrival: Optional[str] = None
    
    # Passenger preferences
    default_adult_count: int = 1
    default_child_count: int = 0
    default_senior_count: int = 0
    default_disability1to3_count: int = 0
    default_disability4to6_count: int = 0
    
    # Reservation options
    passenger_options: list[str] = Field(default=[], sa_column=Column(JSON))  # ["child", "senior", etc.]
    
    # Telegram settings
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_enabled: bool = False
    
    # Payment settings
    card_number: Optional[str] = None  # encrypted
    card_password: Optional[str] = None  # encrypted
    card_birthday: Optional[str] = None  # encrypted
    card_expire: Optional[str] = None  # encrypted
    auto_payment: bool = False


class UserSettings(UserSettingsBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserSettingsCreate(UserSettingsBase):
    pass


class UserSettingsRead(UserSettingsBase):
    id: int
    created_at: datetime
    updated_at: datetime


class UserSettingsUpdate(SQLModel):
    rail_type: Optional[str] = None
    login_id: Optional[str] = None
    encrypted_password: Optional[str] = None
    favorite_stations: Optional[list[str]] = None
    default_departure: Optional[str] = None
    default_arrival: Optional[str] = None
    default_adult_count: Optional[int] = None
    default_child_count: Optional[int] = None
    default_senior_count: Optional[int] = None
    default_disability1to3_count: Optional[int] = None
    default_disability4to6_count: Optional[int] = None
    passenger_options: Optional[list[str]] = None
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_enabled: Optional[bool] = None
    card_number: Optional[str] = None
    card_password: Optional[str] = None
    card_birthday: Optional[str] = None
    card_expire: Optional[str] = None
    auto_payment: Optional[bool] = None