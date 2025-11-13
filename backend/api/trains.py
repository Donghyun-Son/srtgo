"""Train API endpoints for searching trains."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from backend.models.database import get_db
from backend.models.user import User
from backend.models.credential import TrainCredential
from backend.schemas.reservation import TrainSearchRequest, TrainSearchResponse, TrainInfo
from backend.core.dependencies import get_current_active_user
from backend.core.security import credential_encryption
from backend.services.train_service import TrainService

router = APIRouter(prefix="/api/trains", tags=["Trains"])


@router.post("/search", response_model=TrainSearchResponse)
async def search_trains(
    search_request: TrainSearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Search for available trains."""
    # Get train credentials
    result = await db.execute(
        select(TrainCredential).where(
            TrainCredential.user_id == current_user.id,
            TrainCredential.train_type == search_request.train_type
        )
    )
    credential = result.scalar_one_or_none()

    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{search_request.train_type} credentials not found. Please add credentials first."
        )

    # Decrypt credentials
    try:
        user_id = credential_encryption.decrypt(credential.encrypted_user_id)
        password = credential_encryption.decrypt(credential.encrypted_password)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to decrypt credentials"
        )

    # Login and search
    train_service = TrainService()
    success, message = await train_service.login(search_request.train_type, user_id, password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login failed: {message}"
        )

    try:
        trains = await train_service.search_trains(
            search_request.train_type,
            search_request.departure_station,
            search_request.arrival_station,
            search_request.departure_date,
            search_request.departure_time,
            {"adult": 1}  # Default to 1 adult for search
        )

        # Convert trains to response format
        train_infos = []
        for train in trains:
            # Check if seats are available
            available = False
            seat_types_available = []

            # Try to get seat availability info from train object
            if hasattr(train, 'seat_available'):
                available = train.seat_available()
                if available and hasattr(train, 'available_seats'):
                    seat_types_available = list(train.available_seats.keys())

            train_info = TrainInfo(
                train_number=str(getattr(train, 'train_number', getattr(train, 'train_no', 'Unknown'))),
                train_name=str(getattr(train, 'train_name', getattr(train, 'train_type', 'Unknown'))),
                departure_time=str(getattr(train, 'dep_time', '')),
                arrival_time=str(getattr(train, 'arr_time', '')),
                available=available,
                seat_types_available=seat_types_available
            )
            train_infos.append(train_info)

        return TrainSearchResponse(
            trains=train_infos,
            search_date=search_request.departure_date,
            departure_station=search_request.departure_station,
            arrival_station=search_request.arrival_station
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
    finally:
        train_service.logout(search_request.train_type)


@router.get("/stations/{train_type}", response_model=List[str])
async def get_stations(
    train_type: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get list of available stations for a train type."""
    # Import station list from CLI module
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

    from srtgo.srtgo import STATIONS

    if train_type not in ["SRT", "KTX"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid train type. Must be 'SRT' or 'KTX'"
        )

    return STATIONS.get(train_type, [])
