"""Credentials API endpoints for managing user credentials."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from backend.models.database import get_db
from backend.models.user import User
from backend.models.credential import TrainCredential, CardCredential, TelegramCredential
from backend.schemas.credential import (
    TrainCredentialCreate,
    TrainCredentialResponse,
    CardCredentialCreate,
    CardCredentialResponse,
    TelegramCredentialCreate,
    TelegramCredentialResponse,
)
from backend.core.dependencies import get_current_active_user
from backend.core.security import credential_encryption

router = APIRouter(prefix="/api/credentials", tags=["Credentials"])


# Train Credentials
@router.post("/train", response_model=TrainCredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_train_credential(
    credential_data: TrainCredentialCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create or update train credentials."""
    # Check if credential already exists for this train type
    result = await db.execute(
        select(TrainCredential).where(
            TrainCredential.user_id == current_user.id,
            TrainCredential.train_type == credential_data.train_type
        )
    )
    existing_credential = result.scalar_one_or_none()

    # Encrypt sensitive data
    encrypted_user_id = credential_encryption.encrypt(credential_data.user_id)
    encrypted_password = credential_encryption.encrypt(credential_data.password)

    if existing_credential:
        # Update existing
        existing_credential.encrypted_user_id = encrypted_user_id
        existing_credential.encrypted_password = encrypted_password
        existing_credential.preferences = credential_data.preferences
        credential = existing_credential
    else:
        # Create new
        credential = TrainCredential(
            user_id=current_user.id,
            train_type=credential_data.train_type,
            encrypted_user_id=encrypted_user_id,
            encrypted_password=encrypted_password,
            preferences=credential_data.preferences
        )
        db.add(credential)

    await db.commit()
    await db.refresh(credential)

    return credential


@router.get("/train", response_model=List[TrainCredentialResponse])
async def get_train_credentials(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all train credentials for current user."""
    result = await db.execute(
        select(TrainCredential).where(TrainCredential.user_id == current_user.id)
    )
    credentials = result.scalars().all()
    return credentials


# Card Credentials
@router.post("/card", response_model=CardCredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_card_credential(
    credential_data: CardCredentialCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create or update card credentials."""
    # Encrypt sensitive data
    encrypted_card_number = credential_encryption.encrypt(credential_data.card_number)
    encrypted_card_password = credential_encryption.encrypt(credential_data.card_password)
    encrypted_birthday = credential_encryption.encrypt(credential_data.birthday)
    encrypted_expire = credential_encryption.encrypt(credential_data.expire)

    # Get last 4 digits for display
    card_last4 = credential_data.card_number[-4:]

    # Check if credential already exists
    result = await db.execute(
        select(CardCredential).where(CardCredential.user_id == current_user.id)
    )
    existing_credential = result.scalar_one_or_none()

    if existing_credential:
        # Update existing
        existing_credential.encrypted_card_number = encrypted_card_number
        existing_credential.encrypted_card_password = encrypted_card_password
        existing_credential.encrypted_birthday = encrypted_birthday
        existing_credential.encrypted_expire = encrypted_expire
        existing_credential.card_last4 = card_last4
        existing_credential.card_nickname = credential_data.card_nickname
        credential = existing_credential
    else:
        # Create new
        credential = CardCredential(
            user_id=current_user.id,
            encrypted_card_number=encrypted_card_number,
            encrypted_card_password=encrypted_card_password,
            encrypted_birthday=encrypted_birthday,
            encrypted_expire=encrypted_expire,
            card_last4=card_last4,
            card_nickname=credential_data.card_nickname
        )
        db.add(credential)

    await db.commit()
    await db.refresh(credential)

    return credential


@router.get("/card", response_model=CardCredentialResponse)
async def get_card_credential(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get card credential for current user."""
    result = await db.execute(
        select(CardCredential).where(CardCredential.user_id == current_user.id)
    )
    credential = result.scalar_one_or_none()

    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card credential not found"
        )

    return credential


# Telegram Credentials
@router.post("/telegram", response_model=TelegramCredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_telegram_credential(
    credential_data: TelegramCredentialCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create or update Telegram credentials."""
    # Encrypt sensitive data
    encrypted_token = credential_encryption.encrypt(credential_data.token)
    encrypted_chat_id = credential_encryption.encrypt(credential_data.chat_id)

    # Check if credential already exists
    result = await db.execute(
        select(TelegramCredential).where(TelegramCredential.user_id == current_user.id)
    )
    existing_credential = result.scalar_one_or_none()

    if existing_credential:
        # Update existing
        existing_credential.encrypted_token = encrypted_token
        existing_credential.encrypted_chat_id = encrypted_chat_id
        existing_credential.is_enabled = credential_data.is_enabled
        credential = existing_credential
    else:
        # Create new
        credential = TelegramCredential(
            user_id=current_user.id,
            encrypted_token=encrypted_token,
            encrypted_chat_id=encrypted_chat_id,
            is_enabled=credential_data.is_enabled
        )
        db.add(credential)

    await db.commit()
    await db.refresh(credential)

    return credential


@router.get("/telegram", response_model=TelegramCredentialResponse)
async def get_telegram_credential(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get Telegram credential for current user."""
    result = await db.execute(
        select(TelegramCredential).where(TelegramCredential.user_id == current_user.id)
    )
    credential = result.scalar_one_or_none()

    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telegram credential not found"
        )

    return credential
