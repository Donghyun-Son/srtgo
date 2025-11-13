"""Reservation model for tracking train reservations."""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from .database import Base


class ReservationStatus(str, enum.Enum):
    """Reservation status enum."""
    PENDING = "pending"  # Waiting for available train
    SEARCHING = "searching"  # Actively searching/polling
    RESERVED = "reserved"  # Successfully reserved
    PAID = "paid"  # Payment completed
    CANCELLED = "cancelled"  # Cancelled by user
    FAILED = "failed"  # Reservation failed
    EXPIRED = "expired"  # Reservation expired


class Reservation(Base):
    """Reservation model for train bookings."""

    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Train type and service
    train_type = Column(String(10), nullable=False)  # 'SRT' or 'KTX'

    # Travel details
    departure_station = Column(String(50), nullable=False)
    arrival_station = Column(String(50), nullable=False)
    departure_date = Column(String(20), nullable=False)
    departure_time = Column(String(10), nullable=False)

    # Passenger counts (JSON: {adult: 1, child: 0, senior: 0, ...})
    passengers = Column(JSON, nullable=False)

    # Selected trains (JSON: list of train numbers to search for)
    selected_trains = Column(JSON, nullable=True)

    # Seat preference
    seat_type = Column(String(50), nullable=True)

    # Status
    status = Column(Enum(ReservationStatus), default=ReservationStatus.PENDING, nullable=False)

    # Auto payment
    auto_payment = Column(Boolean, default=False, nullable=False)

    # Result data (JSON: reservation details from API)
    result_data = Column(JSON, nullable=True)

    # Error information
    error_message = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="reservations")

    def __repr__(self):
        return f"<Reservation(id={self.id}, user_id={self.user_id}, status={self.status})>"
