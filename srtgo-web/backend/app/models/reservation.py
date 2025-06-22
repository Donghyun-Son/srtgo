from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field, JSON, Column


class ReservationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReservationBase(SQLModel):
    user_id: int = Field(foreign_key="user.id")
    task_id: Optional[str] = None  # Celery task ID
    
    # Train information
    rail_type: str  # "SRT" or "KTX"
    departure_station: str
    arrival_station: str
    departure_date: str  # YYYYMMDD
    departure_time: str  # HHMMSS
    
    # Passenger information
    passengers: dict = Field(default={}, sa_column=Column(JSON))  # {"adult": 1, "child": 0, ...}
    
    # Seat preferences
    seat_type: str  # "GENERAL_FIRST", "GENERAL_ONLY", "SPECIAL_FIRST", "SPECIAL_ONLY"
    
    # Selected trains
    selected_trains: list[int] = Field(default=[], sa_column=Column(JSON))  # Train indices
    
    # Reservation options
    auto_payment: bool = False
    
    # Status tracking
    status: ReservationStatus = ReservationStatus.PENDING
    progress_message: Optional[str] = None
    attempt_count: int = 0
    
    # Result information
    reserved_train_info: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    error_message: Optional[str] = None


class Reservation(ReservationBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class ReservationCreate(SQLModel):
    """Model for creating reservations via API (user_id is set automatically)"""
    # Train information
    rail_type: str  # "SRT" or "KTX"
    departure_station: str
    arrival_station: str
    departure_date: str  # YYYYMMDD
    departure_time: str  # HHMMSS
    
    # Passenger information
    passengers: dict = Field(default_factory=dict)  # {"adult": 1, "child": 0, ...}
    
    # Seat preferences
    seat_type: str  # "GENERAL_FIRST", "GENERAL_ONLY", "SPECIAL_FIRST", "SPECIAL_ONLY"
    
    # Selected trains
    selected_trains: list[int] = Field(default_factory=list)  # Train indices
    
    # Reservation options
    auto_payment: bool = False


class ReservationRead(ReservationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]


class ReservationUpdate(SQLModel):
    task_id: Optional[str] = None
    status: Optional[ReservationStatus] = None
    progress_message: Optional[str] = None
    attempt_count: Optional[int] = None
    reserved_train_info: Optional[dict] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None