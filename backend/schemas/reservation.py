"""Reservation schemas for train booking."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from backend.models.reservation import ReservationStatus


class PassengerCounts(BaseModel):
    """Schema for passenger counts."""
    adult: int = Field(1, ge=1, le=9)
    child: int = Field(0, ge=0, le=9)
    senior: int = Field(0, ge=0, le=9)
    disability1to3: int = Field(0, ge=0, le=9)
    disability4to6: int = Field(0, ge=0, le=9)


class TrainSearchRequest(BaseModel):
    """Schema for searching available trains."""
    train_type: str = Field(..., pattern="^(SRT|KTX)$")
    departure_station: str
    arrival_station: str
    departure_date: str = Field(..., pattern=r"^\d{8}$")  # YYYYMMDD
    departure_time: str = Field(..., pattern=r"^\d{6}$")  # HHMMSS


class TrainInfo(BaseModel):
    """Schema for train information."""
    train_number: str
    train_name: str
    departure_time: str
    arrival_time: str
    available: bool
    seat_types_available: List[str] = []


class TrainSearchResponse(BaseModel):
    """Schema for train search results."""
    trains: List[TrainInfo]
    search_date: str
    departure_station: str
    arrival_station: str


class ReservationCreate(BaseModel):
    """Schema for creating a reservation."""
    train_type: str = Field(..., pattern="^(SRT|KTX)$")
    departure_station: str
    arrival_station: str
    departure_date: str = Field(..., pattern=r"^\d{8}$")  # YYYYMMDD
    departure_time: str = Field(..., pattern=r"^\d{6}$")  # HHMMSS
    passengers: PassengerCounts
    selected_trains: Optional[List[str]] = None  # List of train numbers
    seat_type: Optional[str] = None
    auto_payment: bool = False


class ReservationUpdate(BaseModel):
    """Schema for updating a reservation."""
    status: Optional[ReservationStatus] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class ReservationResponse(BaseModel):
    """Schema for reservation response."""
    id: int
    user_id: int
    train_type: str
    departure_station: str
    arrival_station: str
    departure_date: str
    departure_time: str
    passengers: Dict[str, int]
    selected_trains: Optional[List[str]] = None
    seat_type: Optional[str] = None
    status: ReservationStatus
    auto_payment: bool
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        use_enum_values = True
