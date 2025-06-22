import asyncio
import time
from datetime import datetime
from celery import current_task
from sqlmodel import Session, select
from app.tasks.celery_app import celery_app
from app.core.database import engine
from app.models import Reservation, ReservationStatus
from app.services.websocket import connection_manager
from app.services.reservation_service import ReservationService

def send_websocket_message(message: dict, user_id: str):
    """Send WebSocket message from Celery worker"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(connection_manager.send_personal_message(message, user_id))
        loop.close()
    except Exception as e:
        print(f"Failed to send WebSocket message: {e}")


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
        send_websocket_message(
            {
                "type": "reservation_update",
                "reservation_id": reservation_id,
                "status": "running",
                "message": "예매 시작 중..."
            },
            str(reservation.user_id)
        )
        
        try:
            # For external auth (SRT/KTX login), users are virtual and not stored in DB
            # Extract username from the virtual user_id using the same algorithm from auth.py
            # user_id = int(hashlib.md5(f"{rail_type}_{username}".encode()).hexdigest()[:8], 16)
            
            # Try to find user in database first (for regular DB users)
            from app.models import User
            user_statement = select(User).where(User.id == reservation.user_id)
            user = session.exec(user_statement).first()
            
            if not user:
                # This is a virtual user from external auth (SRT/KTX login)
                # Find user session using Redis SessionManager
                try:
                    from app.services.redis_session_manager import redis_session_manager as session_manager
                    import hashlib
                    
                    rail_type = reservation.rail_type
                    user_id = reservation.user_id
                    found_username = None
                    found_user_key = None
                    
                    print(f"DEBUG: Looking for virtual user - user_id: {user_id}, rail_type: {rail_type}")
                    
                    # Get all Redis session keys
                    r = session_manager.redis_client
                    pattern = "session:*"
                    keys = r.keys(pattern)
                    
                    print(f"DEBUG: Found Redis keys: {keys}")
                    
                    for key in keys:
                        if isinstance(key, bytes):
                            key = key.decode('utf-8')
                        
                        # Extract user_key from Redis key: "session:srt_username" -> "srt_username"
                        if key.startswith("session:"):
                            potential_user_key = key[8:]  # Remove "session:" prefix
                            
                            # Get session info to verify rail_type and reconstruct username
                            session_info = session_manager.get_session_info(potential_user_key)
                            if session_info and session_info.get('rail_type') == rail_type:
                                # Extract username from user_key: "srt_username" -> "username"
                                if potential_user_key.startswith(f"{rail_type.lower()}_"):
                                    potential_username = potential_user_key[len(f"{rail_type.lower()}_"):]
                                    
                                    # Verify this username generates the same user_id
                                    unique_string = f"{rail_type.upper()}_{potential_username}"
                                    test_user_id = int(hashlib.md5(unique_string.encode()).hexdigest()[:8], 16)
                                    
                                    print(f"DEBUG: Testing username={potential_username}, generated_id={test_user_id}, target_id={user_id}")
                                    
                                    if test_user_id == user_id:
                                        found_username = potential_username
                                        found_user_key = potential_user_key
                                        break
                    
                    if not found_username:
                        raise Exception(f"가상 사용자 정보를 복원할 수 없습니다. user_id: {user_id}, rail_type: {rail_type}")
                    
                    # Create a mock user object with the found username
                    class VirtualUser:
                        def __init__(self, username, user_id, rail_type, user_key):
                            self.id = user_id
                            self.username = username
                            self.rail_type = rail_type
                            self.user_key = user_key  # Store user_key for Redis session lookup
                    
                    user = VirtualUser(found_username, user_id, rail_type, found_user_key)
                    print(f"DEBUG: Successfully reconstructed virtual user: username={found_username}, user_id={user_id}, user_key={found_user_key}")
                    
                except Exception as e:
                    print(f"DEBUG: Error reconstructing virtual user: {e}")
                    import traceback
                    traceback.print_exc()
                    raise Exception(f"사용자 정보를 찾을 수 없습니다: {str(e)}")
            
            # Initialize reservation service with user_key for Redis session lookup
            user_key = getattr(user, 'user_key', f"{reservation.rail_type.lower()}_{getattr(user, 'username', 'unknown')}")
            service = ReservationService(user_key=user_key, rail_type=reservation.rail_type)
            
            # Set progress callback with error handling
            def safe_progress_callback(progress_data):
                try:
                    if isinstance(progress_data, dict):
                        message = progress_data.get('message', '')
                        attempt_count = progress_data.get('attempt_count', 0)
                    elif isinstance(progress_data, str):
                        # Handle case where a string is passed instead of dict
                        message = progress_data
                        attempt_count = 0
                        print(f"WARNING: String passed to callback instead of dict: {progress_data}")
                    else:
                        # Handle unexpected types
                        message = str(progress_data)
                        attempt_count = 0
                        print(f"WARNING: Unexpected type passed to callback: {type(progress_data)} - {progress_data}")
                    
                    update_progress(reservation_id, message, attempt_count, session)
                except Exception as e:
                    print(f"ERROR in progress callback: {e}")
                    print(f"progress_data type: {type(progress_data)}")
                    print(f"progress_data content: {progress_data}")
                    # Still call update_progress with error info
                    update_progress(reservation_id, f"콜백 오류: {str(e)}", 0, session)
            
            service.set_progress_callback(safe_progress_callback)
            
            # Prepare parameters for start_reservation
            search_params = {
                'dep': reservation.departure_station,
                'arr': reservation.arrival_station,
                'date': reservation.departure_date,
                'time': reservation.departure_time
            }
            
            # Parse passengers info
            passengers_list = []
            if reservation.passengers['adult'] > 0:
                passengers_list.extend(['Adult'] * reservation.passengers['adult'])
            if reservation.passengers['child'] > 0:
                passengers_list.extend(['Child'] * reservation.passengers['child'])
            if reservation.passengers['senior'] > 0:
                passengers_list.extend(['Senior'] * reservation.passengers['senior'])
            if reservation.passengers['disability1to3'] > 0:
                passengers_list.extend(['Disability1To3'] * reservation.passengers['disability1to3'])
            if reservation.passengers['disability4to6'] > 0:
                passengers_list.extend(['Disability4To6'] * reservation.passengers['disability4to6'])
            
            # Start reservation process (convert async to sync)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(service.start_reservation(
                search_params=search_params,
                selected_trains=reservation.selected_trains,
                passengers=passengers_list,
                seat_type=reservation.seat_type,
                auto_payment=reservation.auto_payment,
                debug=False
            ))
            loop.close()
            
            if result.get("success"):
                # Reservation successful
                reservation.status = ReservationStatus.SUCCESS
                reservation.progress_message = "예매 성공!"
                reservation.reserved_train_info = result.get("train_info")
                reservation.completed_at = datetime.utcnow()
                
                # Send success notification
                send_websocket_message(
                    {
                        "type": "reservation_success",
                        "reservation_id": reservation_id,
                        "train_info": result.get("train_info"),
                        "message": "🎉 예매 성공! 🎉"
                    },
                    str(reservation.user_id)
                )
                
            else:
                # Reservation failed
                reservation.status = ReservationStatus.FAILED
                reservation.error_message = result.get("error", "알 수 없는 오류")
                reservation.completed_at = datetime.utcnow()
                
                # Send failure notification
                send_websocket_message(
                    {
                        "type": "reservation_failed",
                        "reservation_id": reservation_id,
                        "error": result.get("error"),
                        "message": "예매 실패"
                    },
                    str(reservation.user_id)
                )
            
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
            send_websocket_message(
                {
                    "type": "reservation_error",
                    "reservation_id": reservation_id,
                    "error": str(e),
                    "message": "예매 중 오류 발생"
                },
                str(reservation.user_id)
            )
            
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
        send_websocket_message(
            {
                "type": "reservation_progress",
                "reservation_id": reservation_id,
                "message": message,
                "attempt_count": attempt_count
            },
            str(reservation.user_id)
        )