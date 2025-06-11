import asyncio
import time
from datetime import datetime
from celery import current_task
from sqlmodel import Session, select
from app.tasks.celery_app import celery_app
from app.core.database import engine
from app.models import Reservation, ReservationStatus
from app.services.websocket import connection_manager
from app.srtgo_wrapper.reservation_service import ReservationService


@celery_app.task(bind=True)
def start_reservation_task(self, reservation_id: int):
    """Start reservation process in background"""
    
    with Session(engine) as session:
        # Get reservation from database
        statement = select(Reservation).where(Reservation.id == reservation_id)
        reservation = session.exec(statement).first()
        
        if not reservation:
            return {"error": "Reservation not found"}
        
        # Update status to running
        reservation.status = ReservationStatus.RUNNING
        reservation.progress_message = "예매 시작 중..."
        session.add(reservation)
        session.commit()
        
        # Send WebSocket update
        asyncio.run(connection_manager.send_personal_message(
            {
                "type": "reservation_update",
                "reservation_id": reservation_id,
                "status": "running",
                "message": "예매 시작 중..."
            },
            str(reservation.user_id)
        ))
        
        try:
            # Initialize reservation service
            service = ReservationService()
            
            # Start reservation process
            result = service.start_reservation(
                reservation=reservation,
                progress_callback=lambda msg, count=0: update_progress(
                    reservation_id, msg, count, session
                )
            )
            
            if result.get("success"):
                # Reservation successful
                reservation.status = ReservationStatus.SUCCESS
                reservation.progress_message = "예매 성공!"
                reservation.reserved_train_info = result.get("train_info")
                reservation.completed_at = datetime.utcnow()
                
                # Send success notification
                asyncio.run(connection_manager.send_personal_message(
                    {
                        "type": "reservation_success",
                        "reservation_id": reservation_id,
                        "train_info": result.get("train_info"),
                        "message": "🎉 예매 성공! 🎉"
                    },
                    str(reservation.user_id)
                ))
                
            else:
                # Reservation failed
                reservation.status = ReservationStatus.FAILED
                reservation.error_message = result.get("error", "알 수 없는 오류")
                reservation.completed_at = datetime.utcnow()
                
                # Send failure notification
                asyncio.run(connection_manager.send_personal_message(
                    {
                        "type": "reservation_failed",
                        "reservation_id": reservation_id,
                        "error": result.get("error"),
                        "message": "예매 실패"
                    },
                    str(reservation.user_id)
                ))
            
            session.add(reservation)
            session.commit()
            return result
            
        except Exception as e:
            # Handle unexpected errors
            reservation.status = ReservationStatus.FAILED
            reservation.error_message = str(e)
            reservation.completed_at = datetime.utcnow()
            session.add(reservation)
            session.commit()
            
            # Send error notification
            asyncio.run(connection_manager.send_personal_message(
                {
                    "type": "reservation_error",
                    "reservation_id": reservation_id,
                    "error": str(e),
                    "message": "예매 중 오류 발생"
                },
                str(reservation.user_id)
            ))
            
            return {"error": str(e)}


def update_progress(reservation_id: int, message: str, attempt_count: int, session: Session):
    """Update reservation progress"""
    statement = select(Reservation).where(Reservation.id == reservation_id)
    reservation = session.exec(statement).first()
    
    if reservation:
        reservation.progress_message = message
        reservation.attempt_count = attempt_count
        session.add(reservation)
        session.commit()
        
        # Send WebSocket update
        asyncio.run(connection_manager.send_personal_message(
            {
                "type": "reservation_progress",
                "reservation_id": reservation_id,
                "message": message,
                "attempt_count": attempt_count
            },
            str(reservation.user_id)
        ))