from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from pydantic import BaseModel
from app.core.database import get_session
from app.models import User, UserSettings, UserSettingsCreate, UserSettingsRead, UserSettingsUpdate
from app.services.auth import get_current_user
from app.services.settings import SettingsService

router = APIRouter()


class TrainSearchRequest(BaseModel):
    departure: str
    arrival: str
    date: str
    time: Optional[str] = "000000"
    available_only: Optional[bool] = True
    include_no_seats: Optional[bool] = False


@router.get("/", response_model=List[UserSettingsRead])
def get_user_settings(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all settings for current user"""
    service = SettingsService(session)
    return service.get_user_settings(current_user.id)


@router.get("/{rail_type}", response_model=UserSettingsRead)
def get_user_settings_by_rail_type(
    rail_type: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get settings for specific rail type"""
    service = SettingsService(session)
    settings = service.get_settings_by_rail_type(current_user.id, rail_type)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings


@router.post("/", response_model=UserSettingsRead)
def create_user_settings(
    settings: UserSettingsCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create new user settings"""
    service = SettingsService(session)
    return service.create_settings(current_user.id, settings)


@router.put("/{settings_id}", response_model=UserSettingsRead)
def update_user_settings(
    settings_id: int,
    settings_update: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update user settings"""
    service = SettingsService(session)
    db_settings = service.update_settings(current_user.id, settings_id, settings_update)
    if not db_settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return db_settings


@router.delete("/{settings_id}")
def delete_user_settings(
    settings_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete user settings"""
    service = SettingsService(session)
    success = service.delete_settings(current_user.id, settings_id)
    if not success:
        raise HTTPException(status_code=404, detail="Settings not found")
    return {"message": "Settings deleted successfully"}


@router.get("/stations/{rail_type}")
def get_stations(rail_type: str) -> Dict[str, List[str]]:
    """Get station list for rail type"""
    STATIONS = {
        "SRT": [
            "수서", "동탄", "평택지제", "경주", "곡성", "공주", "광주송정", "구례구",
            "김천(구미)", "나주", "남원", "대전", "동대구", "마산", "목포", "밀양",
            "부산", "서대구", "순천", "여수EXPO", "여천", "오송", "울산(통도사)",
            "익산", "전주", "정읍", "진영", "진주", "창원", "창원중앙", "천안아산", "포항"
        ],
        "KTX": [
            "서울", "용산", "영등포", "광명", "수원", "천안아산", "오송", "대전",
            "서대전", "김천구미", "동대구", "경주", "포항", "밀양", "구포", "부산",
            "울산(통도사)", "마산", "창원중앙", "경산", "논산", "익산", "정읍",
            "광주송정", "목포", "전주", "남원", "순천", "여천", "여수EXPO", "구례구", "곡성"
        ]
    }
    
    if rail_type not in STATIONS:
        raise HTTPException(status_code=400, detail="Invalid rail type")
    
    return {"stations": STATIONS[rail_type]}


@router.post("/{rail_type}/test-login")
def test_login_credentials(
    rail_type: str,
    login_data: Dict[str, str],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Test login credentials for rail type"""
    try:
        login_id = login_data.get("login_id")
        password = login_data.get("password")
        
        if not login_id or not password:
            raise HTTPException(status_code=400, detail="Login ID and password required")
        
        # Import here to avoid circular imports
        if rail_type == "SRT":
            from app.srtgo_wrapper.srtgo_compat import test_srt_login
            success, message = test_srt_login(login_id, password)
        elif rail_type == "KTX":
            from app.srtgo_wrapper.srtgo_compat import test_ktx_login
            success, message = test_ktx_login(login_id, password)
        else:
            raise HTTPException(status_code=400, detail="Invalid rail type")
        
        return {"success": success, "message": message}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/{rail_type}/test-telegram")
def test_telegram_notification(
    rail_type: str,
    telegram_data: Dict[str, str],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Test telegram notification"""
    try:
        token = telegram_data.get("token")
        chat_id = telegram_data.get("chat_id")
        
        if not token or not chat_id:
            raise HTTPException(status_code=400, detail="Token and chat_id required")
        
        # Import here to avoid circular imports
        from app.srtgo_wrapper.srtgo_compat import test_telegram
        success, message = test_telegram(token, chat_id)
        
        return {"success": success, "message": message}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/{rail_type}/validate-payment")
def validate_payment_settings(
    rail_type: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Validate payment settings for rail type"""
    try:
        from app.services.payment_service import PaymentService
        
        payment_service = PaymentService(session)
        result = payment_service.validate_payment_settings(current_user.id, rail_type)
        
        return {
            "success": result['valid'],
            "message": result['message']
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/{rail_type}/search-trains")
def search_trains(
    rail_type: str,
    search_data: TrainSearchRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Search trains for specific rail type"""
    try:
        print(f"=== SEARCH TRAINS DEBUG ===")
        print(f"rail_type: {rail_type}")
        print(f"search_data: {search_data}")
        print(f"current_user: {current_user}")
        print(f"current_user.rail_type: {getattr(current_user, 'rail_type', 'NOT_SET')}")
        print(f"=== END DEBUG ===")
        
        # Check if user's rail type matches the requested rail type
        user_rail_type = getattr(current_user, 'rail_type', None)
        if user_rail_type and user_rail_type.upper() != rail_type.upper():
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied. You are logged in with {user_rail_type} account, but trying to access {rail_type} services."
            )
        
        # Try to get cached credentials first (for external auth users)
        from app.services.auth import get_cached_credentials
        # Use the user_key from JWT token if available
        user_key = getattr(current_user, 'user_key', None)
        if not user_key and user_rail_type:
            user_key = f"{user_rail_type.lower()}_{current_user.username}"
        
        credentials = None
        
        print(f"DEBUG: user_key = {user_key}")
        if user_key:
            credentials = get_cached_credentials(user_key)
            print(f"DEBUG: cached credentials = {credentials}")
        
        if not credentials:
            # Fallback to database credentials (for DB-stored users)
            service = SettingsService(session)
            credentials = service.get_decrypted_credentials(current_user.id, rail_type)
            
            if not credentials:
                # For external auth users, try to get session info from session manager
                from app.services.redis_session_manager import redis_session_manager as session_manager
                session_info = session_manager.get_session_info(user_key)
                print(f"DEBUG: session_info from session_manager = {session_info}")
                if session_info:
                    print(f"DEBUG: Using credentials from session manager")
                    credentials = {
                        "login_id": session_info.get("username"),
                        "password": session_info.get("password")  # This should be available in session
                    }
                    print(f"DEBUG: credentials from session = {credentials}")
                else:
                    # Session expired or not found - ask user to re-login
                    from app.core.error_handler import SessionExpiredException
                    raise SessionExpiredException("세션이 만료되었습니다. 다시 로그인해주세요.")
        
        departure = search_data.departure
        arrival = search_data.arrival
        date = search_data.date
        time = search_data.time
        
        # Advanced search options
        available_only = search_data.available_only
        include_no_seats = search_data.include_no_seats
        
        if not all([departure, arrival, date]):
            raise HTTPException(status_code=400, detail="Departure, arrival, and date are required")
        
        # Import here to avoid circular imports
        from app.srtgo_wrapper.srtgo_compat import search_trains
        success, result = search_trains(
            rail_type, 
            credentials["login_id"], 
            credentials.get("password", ""),
            departure, 
            arrival, 
            date, 
            time,
            available_only=available_only if rail_type == "SRT" else True,
            include_no_seats=include_no_seats if rail_type == "KTX" else False
        )
        
        print(f"DEBUG: search_trains returned success={success}, result type={type(result)}")
        if success:
            train_count = len(result) if isinstance(result, list) else 0
            print(f"DEBUG: Found {train_count} trains")
            
            # Check if we have no trains and provide helpful message
            if train_count == 0:
                if not available_only and rail_type == "SRT":
                    # User has available_only=False (not showing sold out trains) and got no results
                    response = {
                        "success": True, 
                        "trains": [],
                        "message": "해당 시간대에 예약 가능한 열차가 없습니다. '매진된 열차도 표시' 옵션을 체크하여 더 많은 열차를 확인해보세요."
                    }
                else:
                    # User is showing sold out trains but still got no results
                    response = {
                        "success": True, 
                        "trains": [],
                        "message": "해당 시간대에 운행하는 열차가 없습니다. 다른 시간대나 날짜를 선택해주세요."
                    }
            else:
                response = {"success": True, "trains": result}
                
            print(f"DEBUG: Returning response: {response}")
            return response
        else:
            print(f"DEBUG: Search failed with message: {result}")
            response = {"success": False, "message": result}
            print(f"DEBUG: Returning error response: {response}")
            return response
    except Exception as e:
        print(f"DEBUG: Exception in search_trains: {e}")
        print(f"DEBUG: Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        response = {"success": False, "message": str(e)}
        print(f"DEBUG: Returning exception response: {response}")
        return response