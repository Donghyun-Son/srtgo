from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, Query
from sqlmodel import Session, select, desc
from app.core.database import get_session
from app.models import User, Reservation, ReservationCreate, ReservationRead, ReservationUpdate, ReservationStatus
from app.services.auth import get_current_user
from app.services.reservation_management_service import ReservationManagementService
from app.tasks.reservation import start_reservation_task

router = APIRouter()


@router.get("/", response_model=List[ReservationRead])
@router.get("", response_model=List[ReservationRead])
def get_reservations(
    status: Optional[str] = Query(None, description="Filter by status (pending, running, success, failed, cancelled)"),
    limit: Optional[int] = Query(10, description="Number of results to return"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all reservations for current user with optional filtering and sorting"""
    statement = select(Reservation).where(Reservation.user_id == current_user.id)
    
    # Add status filter if provided
    if status:
        try:
            status_enum = ReservationStatus(status)
            statement = statement.where(Reservation.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    # Order by created_at in descending order (most recent first)
    statement = statement.order_by(desc(Reservation.created_at))
    
    # Apply limit if provided
    if limit:
        statement = statement.limit(limit)
    
    reservations = session.exec(statement).all()
    return reservations


@router.get("/{reservation_id}", response_model=ReservationRead)
@router.get("/{reservation_id}/", response_model=ReservationRead)
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
@router.post("", response_model=ReservationRead)
async def create_reservation(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create new reservation and start background task"""
    try:
        # Get raw request body first
        raw_body = await request.body()
        print(f"=== CREATE RESERVATION DEBUG ===")
        print(f"Raw request body: {raw_body.decode('utf-8')}")
        print(f"Current user: {current_user}")
        print(f"Current user ID: {current_user.id}")
        
        # Parse the JSON manually to see what we're getting
        import json
        raw_data = json.loads(raw_body.decode('utf-8'))
        print(f"Parsed raw data: {raw_data}")
        
        # Now try to create the Pydantic model
        reservation = ReservationCreate(**raw_data)
        print(f"Successfully created ReservationCreate model: {reservation}")
    except Exception as e:
        print(f"Error parsing reservation data: {e}")
        print(f"Error type: {type(e)}")
        raise HTTPException(status_code=422, detail=f"Invalid reservation data: {str(e)}")
    
    try:
        # Convert ReservationCreate to ReservationBase dict and add user_id
        reservation_dict = reservation.model_dump()
        reservation_dict['user_id'] = current_user.id
        print(f"Reservation dict with user_id: {reservation_dict}")
        
        # Create the database model
        db_reservation = Reservation(**reservation_dict)
        print(f"Validated reservation: {db_reservation}")
        
        session.add(db_reservation)
        session.commit()
        session.refresh(db_reservation)
        
        # Start background reservation task
        task = start_reservation_task.delay(db_reservation.id)
        db_reservation.task_id = task.id
        session.add(db_reservation)
        session.commit()
        session.refresh(db_reservation)
        
        print(f"=== RESERVATION CREATED SUCCESSFULLY ===")
        return db_reservation
    except Exception as e:
        print(f"=== RESERVATION CREATE ERROR ===")
        print(f"Error: {e}")
        print(f"Error type: {type(e)}")
        raise


@router.put("/{reservation_id}", response_model=ReservationRead)
@router.put("/{reservation_id}/", response_model=ReservationRead)
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
@router.delete("/{reservation_id}/")
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


@router.get("/all/{rail_type}")
def get_all_reservations(
    rail_type: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Get all external reservations and tickets from SRT/KTX"""
    user_key = f"{rail_type.lower()}_{current_user.username}"
    
    service = ReservationManagementService(session)
    result = service.get_all_reservations(user_key, rail_type)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    return result


@router.post("/cancel/{rail_type}")
async def cancel_external_reservation(
    rail_type: str,
    reservation_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Cancel or refund an external reservation/ticket"""
    user_key = f"{rail_type.lower()}_{current_user.username}"
    
    service = ReservationManagementService(session)
    result = service.cancel_reservation(user_key, rail_type, reservation_data)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    return result


@router.post("/pay/{rail_type}")
async def pay_external_reservation(
    rail_type: str,
    reservation_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Pay for an unpaid external reservation"""
    user_key = f"{rail_type.lower()}_{current_user.username}"
    
    service = ReservationManagementService(session)
    result = service.pay_reservation(user_key, rail_type, reservation_data, current_user.id)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    return result


@router.post("/send-to-telegram/{rail_type}")
async def send_reservations_to_telegram(
    rail_type: str,
    reservations: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Send reservation details to telegram"""
    service = ReservationManagementService(session)
    result = await service.send_reservations_to_telegram(
        current_user.id, 
        rail_type, 
        reservations
    )
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    return result