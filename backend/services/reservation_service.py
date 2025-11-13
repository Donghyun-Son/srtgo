"""Service for managing reservations and polling."""
import asyncio
from typing import Dict, Any, Optional, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from backend.models.reservation import Reservation, ReservationStatus
from backend.models.credential import TrainCredential
from backend.services.train_service import TrainService
from backend.core.security import credential_encryption


class ReservationService:
    """Service for reservation operations and background polling."""

    def __init__(self):
        """Initialize reservation service."""
        self.active_polls: Dict[int, asyncio.Task] = {}

    async def create_reservation(
        self,
        db: AsyncSession,
        user_id: int,
        reservation_data: Dict[str, Any]
    ) -> Reservation:
        """Create a new reservation."""
        reservation = Reservation(
            user_id=user_id,
            train_type=reservation_data['train_type'],
            departure_station=reservation_data['departure_station'],
            arrival_station=reservation_data['arrival_station'],
            departure_date=reservation_data['departure_date'],
            departure_time=reservation_data['departure_time'],
            passengers=reservation_data['passengers'],
            selected_trains=reservation_data.get('selected_trains'),
            seat_type=reservation_data.get('seat_type'),
            auto_payment=reservation_data.get('auto_payment', False),
            status=ReservationStatus.PENDING
        )

        db.add(reservation)
        await db.commit()
        await db.refresh(reservation)

        return reservation

    async def poll_for_availability(
        self,
        reservation_id: int,
        db: AsyncSession,
        callback: Optional[Callable] = None
    ):
        """
        Poll for train availability in background.

        This runs as a background task and updates reservation status.
        """
        try:
            # Get reservation
            result = await db.execute(
                select(Reservation).where(Reservation.id == reservation_id)
            )
            reservation = result.scalar_one_or_none()

            if not reservation:
                return

            # Update status to searching
            reservation.status = ReservationStatus.SEARCHING
            await db.commit()

            # Get train credentials
            result = await db.execute(
                select(TrainCredential).where(
                    TrainCredential.user_id == reservation.user_id,
                    TrainCredential.train_type == reservation.train_type
                )
            )
            credential = result.scalar_one_or_none()

            if not credential:
                reservation.status = ReservationStatus.FAILED
                reservation.error_message = "Train credentials not found"
                await db.commit()
                return

            # Decrypt credentials
            user_id = credential_encryption.decrypt(credential.encrypted_user_id)
            password = credential_encryption.decrypt(credential.encrypted_password)

            # Initialize train service
            train_service = TrainService()
            success, message = await train_service.login(reservation.train_type, user_id, password)

            if not success:
                reservation.status = ReservationStatus.FAILED
                reservation.error_message = f"Login failed: {message}"
                await db.commit()
                return

            # Poll for availability (max 100 attempts with 30 second intervals = 50 minutes)
            max_attempts = 100
            attempt = 0

            while attempt < max_attempts:
                try:
                    # Search for trains
                    trains = await train_service.search_trains(
                        reservation.train_type,
                        reservation.departure_station,
                        reservation.arrival_station,
                        reservation.departure_date,
                        reservation.departure_time,
                        reservation.passengers
                    )

                    # Check if any selected trains are available
                    for train in trains:
                        train_number = str(getattr(train, 'train_number', getattr(train, 'train_no', '')))

                        # If no specific trains selected, try any available train
                        if not reservation.selected_trains or train_number in reservation.selected_trains:
                            # Check if seats are available
                            if hasattr(train, 'seat_available') and train.seat_available():
                                # Try to reserve
                                reserve_success, reserve_obj, reserve_msg = await train_service.reserve_train(
                                    reservation.train_type,
                                    train,
                                    reservation.passengers,
                                    reservation.seat_type
                                )

                                if reserve_success:
                                    # Reservation successful
                                    reservation.status = ReservationStatus.RESERVED
                                    reservation.result_data = {
                                        "train_number": train_number,
                                        "message": reserve_msg,
                                        "timestamp": datetime.utcnow().isoformat()
                                    }
                                    reservation.completed_at = datetime.utcnow()
                                    await db.commit()

                                    # Notify via callback if provided
                                    if callback:
                                        await callback(reservation_id, "success", reserve_obj)

                                    return

                    # No trains available, wait and retry
                    attempt += 1
                    if callback:
                        await callback(reservation_id, "polling", {"attempt": attempt, "max_attempts": max_attempts})

                    await asyncio.sleep(30)  # Wait 30 seconds before next attempt

                except Exception as e:
                    # Log error and continue
                    print(f"Error during polling attempt {attempt}: {str(e)}")
                    attempt += 1
                    await asyncio.sleep(30)

            # Max attempts reached
            reservation.status = ReservationStatus.FAILED
            reservation.error_message = "No available trains found after maximum attempts"
            await db.commit()

            if callback:
                await callback(reservation_id, "failed", None)

        except Exception as e:
            # Update reservation with error
            try:
                result = await db.execute(
                    select(Reservation).where(Reservation.id == reservation_id)
                )
                reservation = result.scalar_one_or_none()

                if reservation:
                    reservation.status = ReservationStatus.FAILED
                    reservation.error_message = str(e)
                    await db.commit()
            except Exception:
                pass

        finally:
            # Cleanup
            if reservation_id in self.active_polls:
                del self.active_polls[reservation_id]

    def start_polling(
        self,
        reservation_id: int,
        db: AsyncSession,
        callback: Optional[Callable] = None
    ):
        """Start background polling for a reservation."""
        task = asyncio.create_task(
            self.poll_for_availability(reservation_id, db, callback)
        )
        self.active_polls[reservation_id] = task
        return task

    def stop_polling(self, reservation_id: int):
        """Stop background polling for a reservation."""
        if reservation_id in self.active_polls:
            task = self.active_polls[reservation_id]
            task.cancel()
            del self.active_polls[reservation_id]

    def is_polling(self, reservation_id: int) -> bool:
        """Check if a reservation is currently being polled."""
        return reservation_id in self.active_polls


# Global instance
reservation_service = ReservationService()
