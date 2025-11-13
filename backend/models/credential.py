"""Credential models for storing encrypted user credentials."""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .database import Base


class TrainCredential(Base):
    """Store encrypted train service (SRT/KTX) login credentials."""

    __tablename__ = "train_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    train_type = Column(String(10), nullable=False)  # 'SRT' or 'KTX'

    # Encrypted fields
    encrypted_user_id = Column(Text, nullable=False)  # Login ID
    encrypted_password = Column(Text, nullable=False)

    # Travel preferences (stored as JSON)
    preferences = Column(JSON, nullable=True)  # departure, arrival, favorite_stations, etc.

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="train_credentials")

    def __repr__(self):
        return f"<TrainCredential(id={self.id}, user_id={self.user_id}, train_type={self.train_type})>"


class CardCredential(Base):
    """Store encrypted card payment information."""

    __tablename__ = "card_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Card info (all encrypted)
    encrypted_card_number = Column(Text, nullable=False)
    encrypted_card_password = Column(Text, nullable=False)
    encrypted_birthday = Column(Text, nullable=False)
    encrypted_expire = Column(Text, nullable=False)

    # Optional display info (last 4 digits, not encrypted)
    card_last4 = Column(String(4), nullable=True)
    card_nickname = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="card_credentials")

    def __repr__(self):
        return f"<CardCredential(id={self.id}, user_id={self.user_id}, last4={self.card_last4})>"


class TelegramCredential(Base):
    """Store Telegram notification credentials."""

    __tablename__ = "telegram_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Telegram settings
    encrypted_token = Column(Text, nullable=False)
    encrypted_chat_id = Column(Text, nullable=False)
    is_enabled = Column(String(10), default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="telegram_credentials")

    def __repr__(self):
        return f"<TelegramCredential(id={self.id}, user_id={self.user_id})>"
