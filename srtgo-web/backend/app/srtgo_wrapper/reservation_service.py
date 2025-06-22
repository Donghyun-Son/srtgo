import sys
import os
import time
import importlib
import asyncio
from datetime import datetime
from typing import Dict, Any, Callable, Optional, List
from random import gammavariate

# Add srtgo modules to path
# Check if running in Docker (with /app/srtgo path)
if os.path.exists('/app/srtgo'):
    sys.path.append('/app')
else:
    # Local development path
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../srtgo'))

# Apply comprehensive curl_cffi patches before any imports

# Pre-patch curl_cffi before srtgo imports it
try:
    # First try to patch curl_cffi.requests.exceptions
    import curl_cffi.requests.exceptions
    if not hasattr(curl_cffi.requests.exceptions, 'ConnectionError'):
        class ConnectionError(curl_cffi.requests.exceptions.RequestsError):
            """A Connection error occurred."""
            pass
        curl_cffi.requests.exceptions.ConnectionError = ConnectionError
        print("DEBUG: Applied ConnectionError patch for curl_cffi")
except Exception as e:
    print(f"DEBUG: ConnectionError patch failed: {e}")

# Now patch curl_cffi module itself
try:
    import curl_cffi
    import curl_cffi.requests
    
    # Patch Session directly to the main module
    if not hasattr(curl_cffi, 'Session'):
        curl_cffi.Session = curl_cffi.requests.Session
        print("DEBUG: Applied Session patch for curl_cffi")
    
    # Also patch Session with improved timeout and error handling
    original_session_init = curl_cffi.requests.Session.__init__
    def patched_session_init(self, *args, **kwargs):
        # Remove impersonate if it's causing issues
        if 'impersonate' in kwargs and kwargs['impersonate'] not in ['chrome110', 'chrome100', 'firefox']:
            print(f"DEBUG: Removing unsupported impersonate: {kwargs['impersonate']}")
            kwargs.pop('impersonate')
        
        # Set reasonable timeout defaults if not specified
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 15  # 15 seconds default timeout
            
        return original_session_init(self, *args, **kwargs)
    
    curl_cffi.requests.Session.__init__ = patched_session_init
    
    # Patch request methods to add timeout and retry logic
    original_request = curl_cffi.requests.Session.request
    def patched_request(self, method, url, **kwargs):
        # Set timeout for individual requests
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 10  # 10 seconds per request
            
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                return original_request(self, method, url, **kwargs)
            except Exception as e:
                if attempt == max_retries:
                    raise e
                if 'timeout' in str(e).lower() or 'connection' in str(e).lower():
                    print(f"DEBUG: Request timeout/connection error (attempt {attempt + 1}), retrying...")
                    time.sleep(1)  # Wait 1 second before retry
                    continue
                else:
                    raise e
    
    curl_cffi.requests.Session.request = patched_request
    print("DEBUG: Applied Session timeout and retry patches for curl_cffi")
        
except Exception as e:
    print(f"Warning: Could not apply curl_cffi patches: {e}")

try:
    from srtgo.srt import SRT, SRTError, SeatType, Adult, Child, Senior, Disability1To3, Disability4To6
    from srtgo.ktx import Korail, KorailError, ReserveOption, TrainType, AdultPassenger, ChildPassenger, SeniorPassenger, Disability1To3Passenger, Disability4To6Passenger
    from curl_cffi.requests.exceptions import ConnectionError
    from json.decoder import JSONDecodeError
    import curl_cffi
    print("DEBUG: Successfully imported srtgo modules")
except ImportError as e:
    import json
    print(f"Warning: Could not import srtgo modules: {e}")
    # Create mock classes for development
    class SRT:
        def __init__(self, *args, **kwargs): pass
    class Korail:
        def __init__(self, *args, **kwargs): pass
    class SRTError(Exception): pass
    class KorailError(Exception): pass
    class SeatType:
        GENERAL_FIRST = "GENERAL_FIRST"
    class ReserveOption:
        GENERAL_FIRST = "GENERAL_FIRST"
    # Import JSONDecodeError from standard library as fallback
    JSONDecodeError = json.JSONDecodeError
    ConnectionError = Exception


class ReservationService:
    """Service class to wrap original srtgo functionality for web use"""
    
    def __init__(self, user_key: str = None, rail_type: str = None):
        # Gamma distribution parameters matching original CLI exactly
        self.RESERVE_INTERVAL_SHAPE = 4      # Shape parameter
        self.RESERVE_INTERVAL_SCALE = 0.25   # Scale parameter  
        self.RESERVE_INTERVAL_MIN = 0.25     # Minimum interval (seconds)
        self.WAITING_BAR = ["|", "/", "-", "\\"]
        
        # Track reservation state
        self.is_running = False
        self.attempt_count = 0
        self.start_time = None
        
        # User context for session management
        self.user_key = user_key
        self.rail_type = rail_type
        self.progress_callback = None
    
    def set_progress_callback(self, callback: Callable):
        """Set progress callback for real-time updates"""
        self.progress_callback = callback
    
    async def start_reservation(
        self, 
        search_params: Dict[str, Any],
        selected_trains: List[int],
        passengers: List[str],
        seat_type: str,
        auto_payment: bool = False,
        debug: bool = False
    ) -> Dict[str, Any]:
        """
        Start reservation process based on search parameters
        Returns: {"success": bool, "train_info": dict, "error": str}
        """
        try:
            # Initialize rail client using stored user_key
            rail = self._login_from_session()
            
            if not rail:
                return {"success": False, "error": "로그인 실패 - 세션이 만료되었거나 존재하지 않습니다"}
            
            # Prepare search parameters for srtgo API
            params = self._prepare_search_params(search_params)
            
            # Get passenger classes and build passenger list
            passenger_classes = self._get_passenger_classes(self.rail_type)
            passenger_objects = self._build_passenger_objects(passengers, passenger_classes)
            
            # Initialize reservation state
            self.is_running = True
            self.attempt_count = 0
            self.start_time = time.time()
            
            while self.is_running:
                try:
                    self.attempt_count += 1
                    elapsed_time = time.time() - self.start_time
                    hours, remainder = divmod(int(elapsed_time), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    # Progress message with spinning animation (like original CLI)
                    waiting_char = self.WAITING_BAR[self.attempt_count & 3]
                    progress_msg = f"예매 대기 중... {waiting_char} {self.attempt_count:4d} ({hours:02d}:{minutes:02d}:{seconds:02d})"
                    if self.progress_callback:
                        self.progress_callback({
                            'message': progress_msg,
                            'attempt_count': self.attempt_count
                        })
                    
                    # Search for trains
                    print(f"DEBUG: search_train params = {params}")
                    trains = rail.search_train(**params)
                    
                    if not trains:
                        if self.progress_callback:
                            self.progress_callback({
                                'message': "예약 가능한 열차가 없습니다",
                                'attempt_count': self.attempt_count
                            })
                        self._sleep()
                        continue
                    
                    # Check selected trains for availability
                    for train_idx in selected_trains:
                        if train_idx < len(trains):
                            train = trains[train_idx]
                            if self._is_seat_available(train, seat_type, self.rail_type):
                                # Attempt reservation
                                try:
                                    reserved = rail.reserve(
                                        train, 
                                        passengers=passenger_objects, 
                                        option=self._get_seat_option(seat_type, self.rail_type)
                                    )
                                    
                                    # Success!
                                    train_info = self._format_train_info(reserved)
                                    
                                    # Handle auto payment if enabled
                                    if auto_payment and hasattr(reserved, 'is_waiting') and not reserved.is_waiting:
                                        payment_success = self._pay_card(rail, reserved)
                                        if payment_success:
                                            train_info["payment_status"] = "completed"
                                    
                                    # Send telegram notification
                                    try:
                                        from app.services.telegram_service import TelegramService
                                        from app.core.database import engine
                                        from sqlmodel import Session
                                        
                                        # Get user_id from user_key for telegram
                                        user_id = self._extract_user_id_from_key()
                                        if user_id:
                                            with Session(engine) as telegram_session:
                                                telegram_service = TelegramService(telegram_session)
                                                await telegram_service.send_reservation_success(
                                                    user_id, 
                                                    self.rail_type, 
                                                    train_info
                                                )
                                    except Exception as telegram_ex:
                                        print(f"Failed to send telegram notification: {telegram_ex}")
                                    
                                    return {
                                        "success": True,
                                        "train_info": train_info,
                                        "message": "예매 성공!"
                                    }
                                    
                                except Exception as e:
                                    if self.progress_callback:
                                        self.progress_callback({
                                            'message': f"예매 시도 실패: {str(e)}",
                                            'attempt_count': self.attempt_count
                                        })
                    
                    self._sleep()
                    
                except (SRTError, KorailError) as ex:
                    if not self._handle_reservation_error(ex, rail):
                        return {"success": False, "error": str(ex)}
                    self._sleep()
                    
                except (JSONDecodeError, ConnectionError) as ex:
                    if self.progress_callback:
                        self.progress_callback({
                            'message': f"연결 오류: {str(ex)}",
                            'attempt_count': self.attempt_count
                        })
                    # Re-login on connection errors
                    rail = self._login_from_session()
                    if not rail:
                        return {"success": False, "error": "연결 오류 후 재로그인 실패"}
                    self._sleep()
                    
                except Exception as ex:
                    error_msg = str(ex)
                    
                    # Handle timeout errors specifically
                    if 'timeout' in error_msg.lower() or 'timed out' in error_msg.lower():
                        if self.progress_callback:
                            self.progress_callback({
                                'message': "타임아웃 오류 - 재시도 중...",
                                'attempt_count': self.attempt_count
                            })
                        # Re-login on timeout
                        rail = self._login_from_session()
                        if not rail:
                            return {"success": False, "error": "타임아웃 오류 후 재로그인 실패"}
                        self._sleep()
                        continue
                    
                    # Handle curl connection errors
                    if 'curl:' in error_msg or 'Connection' in error_msg:
                        if self.progress_callback:
                            self.progress_callback({
                                'message': "네트워크 오류 - 재시도 중...",
                                'attempt_count': self.attempt_count
                            })
                        # Re-login on network errors
                        rail = self._login_from_session()
                        if not rail:
                            return {"success": False, "error": "네트워크 오류 후 재로그인 실패"}
                        self._sleep()
                        continue
                    
                    # For other errors, send telegram notification and stop
                    try:
                        from app.services.telegram_service import TelegramService
                        from app.core.database import engine
                        from sqlmodel import Session
                        
                        user_id = self._extract_user_id_from_key()
                        if user_id:
                            with Session(engine) as telegram_session:
                                telegram_service = TelegramService(telegram_session)
                                await telegram_service.send_reservation_error(
                                    user_id, 
                                    self.rail_type, 
                                    error_msg
                                )
                    except Exception as telegram_ex:
                        print(f"Failed to send telegram error notification: {telegram_ex}")
                    
                    return {"success": False, "error": f"예상치 못한 오류: {error_msg}"}
                    
        except Exception as e:
            # Send telegram failure notification
            try:
                from app.services.telegram_service import TelegramService
                from app.core.database import engine
                from sqlmodel import Session
                
                user_id = self._extract_user_id_from_key()
                if user_id:
                    with Session(engine) as telegram_session:
                        telegram_service = TelegramService(telegram_session)
                        await telegram_service.send_reservation_failure(
                            user_id, 
                            self.rail_type, 
                            str(e)
                        )
            except Exception as telegram_ex:
                print(f"Failed to send telegram failure notification: {telegram_ex}")
            
            return {"success": False, "error": f"예매 초기화 실패: {str(e)}"}
    
    def _login_from_session(self) -> Optional[Any]:
        """Get existing session from SessionManager (from web browser login)"""
        try:
            from app.services.redis_session_manager import redis_session_manager as session_manager
            
            print(f"DEBUG: _login_from_session called with user_key={self.user_key}")
            
            # Try to get existing session from Redis SessionManager  
            client = session_manager.get_session(self.user_key)
            
            if client:
                print(f"DEBUG: Found existing {self.rail_type} session")
                return client
            else:
                print(f"DEBUG: No active session found for user_key: {self.user_key}")
                # Get session info for debugging
                session_info = session_manager.get_session_info(self.user_key)
                print(f"DEBUG: Redis session info: {session_info}")
                
                # If we have session info but couldn't create client, it might be expired
                if session_info:
                    print(f"ERROR: Found session info but couldn't create client - session may be expired")
                else:
                    print(f"ERROR: No session found in Redis - user must login via web browser")
                
                return None
                
        except Exception as e:
            print(f"DEBUG: Login error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _prepare_search_params(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """Convert search parameters to srtgo format"""
        # Convert date format from YYYY-MM-DD to YYYYMMDD
        date_formatted = search_params.get('date', '').replace('-', '') if search_params.get('date') else None
        
        # Convert time format from HH:MM to HHMMSS  
        time_formatted = search_params.get('time', '').replace(':', '') + '00' if search_params.get('time') else None
        
        params = {
            "dep": search_params.get('dep'),
            "arr": search_params.get('arr'),
            "date": date_formatted,
            "time": time_formatted,
        }
        
        if self.rail_type == "SRT":
            params["available_only"] = False
        else:
            params["include_no_seats"] = True
            
        return params
    
    def _build_passenger_objects(self, passengers: List[str], passenger_classes: Dict[str, Any]) -> list:
        """Build passenger objects from string list"""
        passenger_objects = []
        passenger_counts = {}
        
        # Count each type
        for p in passengers:
            if p in ['Adult', 'Child', 'Senior', 'Disability1To3', 'Disability4To6']:
                key = p.lower()
                passenger_counts[key] = passenger_counts.get(key, 0) + 1
        
        # Create passenger objects  
        for passenger_type, count in passenger_counts.items():
            if count > 0 and passenger_type in passenger_classes:
                passenger_objects.append(passenger_classes[passenger_type](count))
                
        return passenger_objects
    
    def _extract_user_id_from_key(self) -> Optional[int]:
        """Extract user_id from user_key using the same hash method as auth.py"""
        try:
            if not self.user_key:
                return None
                
            # Extract username from user_key: "srt_username" -> "username"
            if self.user_key.startswith(f"{self.rail_type.lower()}_"):
                username = self.user_key[len(f"{self.rail_type.lower()}_"):]
                
                # Generate user_id using same method as auth.py
                import hashlib
                unique_string = f"{self.rail_type.upper()}_{username}"
                user_id = int(hashlib.md5(unique_string.encode()).hexdigest()[:8], 16)
                return user_id
                
        except Exception as e:
            print(f"Error extracting user_id from key: {e}")
            
        return None
    
    def _build_search_params(self, reservation: Any) -> Dict[str, Any]:
        """Build search parameters from reservation data (legacy method)"""
        # Get passenger classes for search
        rail_type = reservation.rail_type
        passenger_classes = self._get_passenger_classes(rail_type)
        
        # Total passenger count for search
        total_count = sum(reservation.passengers.values())
        
        # Convert date format from YYYY-MM-DD to YYYYMMDD for srtgo
        date_formatted = reservation.departure_date.replace('-', '') if reservation.departure_date else None
        
        # Convert time format from HH:MM to HHMMSS for srtgo  
        time_formatted = reservation.departure_time.replace(':', '') + '00' if reservation.departure_time else None
        
        params = {
            "dep": reservation.departure_station,
            "arr": reservation.arrival_station, 
            "date": date_formatted,
            "time": time_formatted,
            "passengers": [passenger_classes["adult"](total_count)],
        }
        
        if rail_type == "SRT":
            params["available_only"] = False
        else:
            params["include_no_seats"] = True
            # Add KTX-specific options if needed
        
        return params
    
    def _get_passenger_classes(self, rail_type: str) -> Dict[str, Any]:
        """Get passenger classes based on rail type"""
        if rail_type == "SRT":
            return {
                "adult": Adult,
                "child": Child,
                "senior": Senior,
                "disability1to3": Disability1To3,
                "disability4to6": Disability4To6,
            }
        else:
            return {
                "adult": AdultPassenger,
                "child": ChildPassenger,
                "senior": SeniorPassenger,
                "disability1to3": Disability1To3Passenger,
                "disability4to6": Disability4To6Passenger,
            }
    
    def _build_passengers(self, passenger_counts: Dict[str, int], passenger_classes: Dict[str, Any]) -> list:
        """Build passenger list from counts"""
        passengers = []
        for passenger_type, count in passenger_counts.items():
            if count > 0 and passenger_type in passenger_classes:
                passengers.append(passenger_classes[passenger_type](count))
        return passengers
    
    def _get_seat_option(self, seat_type: str, rail_type: str) -> Any:
        """Get seat type option based on rail type"""
        if rail_type == "SRT":
            return getattr(SeatType, seat_type, SeatType.GENERAL_FIRST)
        else:
            return getattr(ReserveOption, seat_type, ReserveOption.GENERAL_FIRST)
    
    def _is_seat_available(self, train: Any, seat_type: str, rail_type: str) -> bool:
        """Check if seat is available for given train"""
        if rail_type == "SRT":
            if not train.seat_available():
                return train.reserve_standby_available()
            if seat_type in ["GENERAL_FIRST", "SPECIAL_FIRST"]:
                return train.seat_available()
            elif seat_type == "GENERAL_ONLY":
                return train.general_seat_available()
            else:
                return train.special_seat_available()
        else:
            if not train.has_seat():
                return train.has_waiting_list()
            if seat_type in ["GENERAL_FIRST", "SPECIAL_FIRST"]:
                return train.has_seat()
            elif seat_type == "GENERAL_ONLY":
                return train.has_general_seat()
            else:
                return train.has_special_seat()
    
    def _format_train_info(self, reservation: Any) -> Dict[str, Any]:
        """Format train information for response"""
        info = {
            "reservation_id": getattr(reservation, 'id', None),
            "train_name": str(reservation),
            "departure_time": getattr(reservation, 'departure_time', None),
            "arrival_time": getattr(reservation, 'arrival_time', None),
            "seat_info": [],
            "payment_status": "pending"
        }
        
        # Add ticket information if available
        if hasattr(reservation, 'tickets') and reservation.tickets:
            for ticket in reservation.tickets:
                info["seat_info"].append(str(ticket))
        
        return info
    
    def _pay_card(self, rail: Any, reservation: Any) -> bool:
        """Attempt automatic card payment using PaymentService"""
        try:
            from app.services.payment_service import PaymentService
            from app.core.database import engine
            from app.models import User
            from sqlmodel import Session, select
            
            with Session(engine) as session:
                # Get user_id from user_key
                user_id = self._extract_user_id_from_key()
                
                if not user_id:
                    print(f"Error: Could not extract user_id from user_key for payment")
                    return False
                
                payment_service = PaymentService(session)
                result = payment_service.process_auto_payment(user_id, reservation, self.rail_type)
                
                if result['success']:
                    print(f"Payment successful: {result['message']}")
                    return True
                else:
                    print(f"Payment failed: {result['message']}")
                    return False
                    
        except Exception as e:
            print(f"Error in _pay_card: {e}")
            return False
    
    def _handle_reservation_error(self, ex: Exception, rail: Any) -> bool:
        """Handle reservation errors with sophisticated logic matching original CLI"""
        msg = str(ex)
        
        if self.rail_type == "SRT":
            # Bot detection - clear session and continue
            if "정상적인 경로로 접근 부탁드립니다" in msg:
                if self.progress_callback:
                    self.progress_callback({
                        'message': "🤖 봇 감지 - 세션 재설정 중...",
                        'attempt_count': self.attempt_count
                    })
                if hasattr(rail, 'clear'):
                    rail.clear()
                return True
                
            # Login required - try to refresh
            elif "로그인 후 사용하십시오" in msg:
                if self.progress_callback:
                    self.progress_callback({
                        'message': "🔐 세션 만료 - 재로그인 시도 중...",
                        'attempt_count': self.attempt_count
                    })
                # In this simplified version, we'll continue and let the main loop handle re-login
                return True
                
            # Expected SRT errors - continue retrying
            elif any(err in msg for err in [
                "잔여석없음",
                "사용자가 많아 접속이 원활하지 않습니다", 
                "예약대기 접수가 마감되었습니다",
                "예약대기자한도수초과"
            ]):
                return True  # Continue retrying
                
            # Unexpected SRT errors - stop
            else:
                if self.progress_callback:
                    self.progress_callback({
                        'message': f"❌ SRT 오류: {msg}",
                        'attempt_count': self.attempt_count
                    })
                return False
                
        elif self.rail_type == "KTX":
            # Expected KTX errors - continue retrying
            if any(err in msg for err in ["Sold out", "잔여석없음", "예약대기자한도수초과"]):
                return True
            else:
                if self.progress_callback:
                    self.progress_callback({
                        'message': f"❌ KTX 오류: {msg}",
                        'attempt_count': self.attempt_count
                    })
                return False
        
        # Unknown rail type or error
        if self.progress_callback:
            self.progress_callback({
                'message': f"⚠️ 알 수 없는 오류: {msg}",
                'attempt_count': self.attempt_count
            })
        return False
    
    def _sleep(self):
        """Sleep with gamma distribution interval matching original CLI"""
        # Gamma distribution: average = SHAPE * SCALE = 4 * 0.25 = 1.0 seconds
        # This creates intervals around 1.25 ± 0.25 seconds like the original
        interval = gammavariate(self.RESERVE_INTERVAL_SHAPE, self.RESERVE_INTERVAL_SCALE) + self.RESERVE_INTERVAL_MIN
        time.sleep(interval)
    
    def stop_reservation(self):
        """Stop the reservation process"""
        self.is_running = False
        if self.progress_callback:
            self.progress_callback({
                'message': "예약이 중단되었습니다",
                'attempt_count': self.attempt_count
            })