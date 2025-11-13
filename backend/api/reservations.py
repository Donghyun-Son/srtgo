"""Reservation API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
import json

from backend.models.database import get_db
from backend.models.user import User
from backend.models.reservation import Reservation, ReservationStatus
from backend.schemas.reservation import ReservationCreate, ReservationResponse, ReservationUpdate
from backend.core.dependencies import get_current_active_user
from backend.services.reservation_service import reservation_service

router = APIRouter(prefix="/api/reservations", tags=["Reservations"])


@router.post("", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_reservation(
    reservation_data: ReservationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new reservation and optionally start polling."""
    # Create reservation
    reservation = await reservation_service.create_reservation(
        db,
        current_user.id,
        reservation_data.dict()
    )

    return reservation


@router.get("", response_model=List[ReservationResponse])
async def get_reservations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50
):
    """Get all reservations for current user."""
    result = await db.execute(
        select(Reservation)
        .where(Reservation.user_id == current_user.id)
        .order_by(desc(Reservation.created_at))
        .limit(limit)
    )
    reservations = result.scalars().all()
    return reservations


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation(
    reservation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific reservation."""
    result = await db.execute(
        select(Reservation).where(
            Reservation.id == reservation_id,
            Reservation.user_id == current_user.id
        )
    )
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )

    return reservation


@router.post("/{reservation_id}/start-polling")
async def start_polling(
    reservation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Start polling for train availability."""
    # Check if reservation exists and belongs to user
    result = await db.execute(
        select(Reservation).where(
            Reservation.id == reservation_id,
            Reservation.user_id == current_user.id
        )
    )
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )

    if reservation.status not in [ReservationStatus.PENDING, ReservationStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start polling for reservation with status: {reservation.status}"
        )

    if reservation_service.is_polling(reservation_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Polling already in progress for this reservation"
        )

    # Start polling in background
    reservation_service.start_polling(reservation_id, db)

    return {"message": "Polling started", "reservation_id": reservation_id}


@router.post("/{reservation_id}/stop-polling")
async def stop_polling(
    reservation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Stop polling for train availability."""
    # Check if reservation exists and belongs to user
    result = await db.execute(
        select(Reservation).where(
            Reservation.id == reservation_id,
            Reservation.user_id == current_user.id
        )
    )
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )

    if not reservation_service.is_polling(reservation_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active polling for this reservation"
        )

    # Stop polling
    reservation_service.stop_polling(reservation_id)

    # Update reservation status
    reservation.status = ReservationStatus.CANCELLED
    await db.commit()

    return {"message": "Polling stopped", "reservation_id": reservation_id}


@router.patch("/{reservation_id}", response_model=ReservationResponse)
async def update_reservation(
    reservation_id: int,
    update_data: ReservationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a reservation."""
    result = await db.execute(
        select(Reservation).where(
            Reservation.id == reservation_id,
            Reservation.user_id == current_user.id
        )
    )
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )

    # Update fields
    if update_data.status:
        reservation.status = update_data.status
    if update_data.result_data:
        reservation.result_data = update_data.result_data
    if update_data.error_message:
        reservation.error_message = update_data.error_message

    await db.commit()
    await db.refresh(reservation)

    return reservation


@router.websocket("/ws/{reservation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    reservation_id: int,
    # Note: WebSocket authentication would need custom implementation
):
    """WebSocket endpoint for real-time reservation updates."""
    await websocket.accept()

    async def callback(res_id: int, status: str, data):
        """Callback to send updates via WebSocket."""
        try:
            await websocket.send_json({
                "reservation_id": res_id,
                "status": status,
                "data": data,
                "timestamp": str(datetime.utcnow())
            })
        except Exception:
            pass

    try:
        while True:
            # Keep connection alive and receive messages
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("action") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for reservation {reservation_id}")
