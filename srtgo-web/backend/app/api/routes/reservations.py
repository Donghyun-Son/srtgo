from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from app.core.database import get_session
from app.models import User, Reservation, ReservationCreate, ReservationRead, ReservationUpdate
from app.services.auth import get_current_user
from app.tasks.reservation import start_reservation_task

router = APIRouter()


@router.get("/", response_model=List[ReservationRead])
def get_reservations(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all reservations for current user"""
    statement = select(Reservation).where(Reservation.user_id == current_user.id)
    reservations = session.exec(statement).all()
    return reservations


@router.get("/{reservation_id}", response_model=ReservationRead)
def get_reservation(
    reservation_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get specific reservation"""
    statement = select(Reservation).where(
        Reservation.id == reservation_id,
        Reservation.user_id == current_user.id
    )
    reservation = session.exec(statement).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return reservation


@router.post("/", response_model=ReservationRead)
def create_reservation(
    reservation: ReservationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create new reservation and start background task"""
    reservation.user_id = current_user.id
    db_reservation = Reservation.model_validate(reservation)
    session.add(db_reservation)
    session.commit()
    session.refresh(db_reservation)
    
    # Start background reservation task
    task = start_reservation_task.delay(db_reservation.id)
    db_reservation.task_id = task.id
    session.add(db_reservation)
    session.commit()
    session.refresh(db_reservation)
    
    return db_reservation


@router.put("/{reservation_id}", response_model=ReservationRead)
def update_reservation(
    reservation_id: int,
    reservation_update: ReservationUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update reservation"""
    statement = select(Reservation).where(
        Reservation.id == reservation_id,
        Reservation.user_id == current_user.id
    )
    db_reservation = session.exec(statement).first()
    if not db_reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    reservation_data = reservation_update.model_dump(exclude_unset=True)
    for key, value in reservation_data.items():
        setattr(db_reservation, key, value)
    
    session.add(db_reservation)
    session.commit()
    session.refresh(db_reservation)
    return db_reservation


@router.delete("/{reservation_id}")
def cancel_reservation(
    reservation_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Cancel reservation"""
    statement = select(Reservation).where(
        Reservation.id == reservation_id,
        Reservation.user_id == current_user.id
    )
    db_reservation = session.exec(statement).first()
    if not db_reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    # Cancel Celery task if running
    if db_reservation.task_id:
        from app.tasks.celery_app import celery_app
        celery_app.control.revoke(db_reservation.task_id, terminate=True)
    
    # Update status
    db_reservation.status = "cancelled"
    session.add(db_reservation)
    session.commit()
    
    return {"message": "Reservation cancelled successfully"}