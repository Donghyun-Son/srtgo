"""
Advanced Reservation Service with Gamma Distribution Retry Logic
Implements sophisticated retry mechanism like the original CLI
"""
import time
import asyncio
from typing import List, Dict, Any, Optional, Callable
from random import gammavariate
from datetime import datetime
from app.services.redis_session_manager import redis_session_manager as session_manager
from app.core.error_handler import handle_srt_error, SRTGoException, BotDetectedException, SessionExpiredException

# Gamma distribution parameters for retry intervals (from original CLI)
RESERVE_INTERVAL_SHAPE = 4      # Shape parameter
RESERVE_INTERVAL_SCALE = 0.25   # Scale parameter  
RESERVE_INTERVAL_MIN = 0.25     # Minimum interval (seconds)

# Average interval = SHAPE * SCALE = 4 * 0.25 = 1.0 seconds
# This creates a gamma distribution around 1.25 ± 0.25 seconds

class ReservationService:
    """
    Advanced reservation service with retry logic matching original CLI
    """
    
    def __init__(self, user_key: str, rail_type: str):
        self.user_key = user_key
        self.rail_type = rail_type.upper()
        self.client = None
        self.is_running = False
        self.attempt_count = 0
        self.start_time = None
        self.progress_callback: Optional[Callable] = None
        
    def set_progress_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Set callback function for progress updates"""
        self.progress_callback = callback
        
    def _emit_progress(self, status: str, message: str, **kwargs):
        """Emit progress update"""
        if self.progress_callback:
            elapsed_time = time.time() - self.start_time if self.start_time else 0
            hours, remainder = divmod(int(elapsed_time), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            progress_data = {
                'status': status,
                'message': message,
                'attempt_count': self.attempt_count,
                'elapsed_time': f"{hours:02d}:{minutes:02d}:{seconds:02d}",
                'elapsed_seconds': elapsed_time,
                **kwargs
            }
            self.progress_callback(progress_data)
    
    def _sleep_gamma(self):
        """Sleep using gamma distribution like original CLI"""
        interval = gammavariate(RESERVE_INTERVAL_SHAPE, RESERVE_INTERVAL_SCALE) + RESERVE_INTERVAL_MIN
        time.sleep(interval)
        
    def _get_client(self):
        """Get or refresh client session"""
        self.client = session_manager.get_session(self.user_key)
        if not self.client:
            raise SessionExpiredException("세션이 만료되었습니다. 다시 로그인해주세요.")
        return self.client
        
    def _is_seat_available(self, train: Any, seat_type: str) -> bool:
        """Check if seat is available for given train and seat type"""
        if self.rail_type == "SRT":
            # SRT seat availability logic
            if not train.seat_available():
                return train.reserve_standby_available()
            
            if seat_type in ['GENERAL_FIRST', 'SPECIAL_FIRST']:
                return train.seat_available()
            elif seat_type == 'GENERAL_ONLY':
                return train.general_seat_available()
            else:  # SPECIAL_ONLY
                return train.special_seat_available()
        else:
            # KTX seat availability logic  
            if not train.has_seat():
                return train.has_waiting_list()
                
            if seat_type in ['GENERAL_FIRST', 'SPECIAL_FIRST']:
                return train.has_seat()
            elif seat_type == 'GENERAL_ONLY':
                return train.has_general_seat()
            else:  # SPECIAL_ONLY
                return train.has_special_seat()
                
    def _handle_reservation_error(self, ex: Exception, debug: bool = False) -> bool:
        """
        Handle reservation errors with sophisticated logic from original CLI
        Returns True to continue, False to stop
        """
        error_msg = str(ex)
        
        # Handle SRT-specific errors
        if self.rail_type == "SRT":
            # Bot detection - clear session and continue
            if "정상적인 경로로 접근 부탁드립니다" in error_msg:
                if debug:
                    print(f"Bot detection error: {ex}")
                self.client.clear() if hasattr(self.client, 'clear') else None
                self._emit_progress('warning', '봇 감지 - 세션 재설정 중...')
                return True
                
            # Login required - refresh session
            elif "로그인 후 사용하십시오" in error_msg:
                if debug:
                    print(f"Login required: {ex}")
                self._emit_progress('warning', '세션 만료 - 재로그인 중...')
                try:
                    self._get_client()  # This will refresh the session
                    return True
                except:
                    self._emit_progress('error', '세션 복구 실패')
                    return False
                    
            # Expected errors - continue retrying
            elif any(err in error_msg for err in [
                "잔여석없음",
                "사용자가 많아 접속이 원활하지 않습니다", 
                "예약대기 접수가 마감되었습니다",
                "예약대기자한도수초과"
            ]):
                return True  # Continue retrying
                
            # Unexpected SRT errors - ask user or stop
            else:
                self._emit_progress('error', f'SRT 오류: {error_msg}')
                # In web version, we'll stop for now (could add user interaction later)
                return False
                
        # Handle KTX-specific errors  
        elif self.rail_type == "KTX":
            # Expected KTX errors - continue retrying
            if any(msg in error_msg for msg in ["Sold out", "잔여석없음", "예약대기자한도수초과"]):
                return True
            else:
                self._emit_progress('error', f'KTX 오류: {error_msg}')
                return False
                
        # Handle connection errors
        elif "ConnectionError" in str(type(ex)) or "연결" in error_msg:
            self._emit_progress('warning', '연결 오류 - 재연결 중...')
            try:
                self._get_client()  # Refresh session
                return True
            except:
                self._emit_progress('error', '연결 복구 실패')
                return False
                
        # Handle JSON decode errors
        elif "JSONDecodeError" in str(type(ex)):
            if debug:
                print(f"JSON decode error: {ex}")
            self._emit_progress('warning', 'JSON 오류 - 세션 재설정 중...')
            try:
                self._get_client()
                return True
            except:
                return False
                
        # Unknown errors
        else:
            if debug:
                print(f"Undefined exception: {ex}")
            self._emit_progress('error', f'알 수 없는 오류: {error_msg}')
            return False
            
    async def start_reservation(self, 
                              search_params: Dict[str, Any],
                              selected_trains: List[int], 
                              passengers: List[Any],
                              seat_type: str,
                              auto_payment: bool = False,
                              debug: bool = False) -> Dict[str, Any]:
        """
        Start reservation process with advanced retry logic
        """
        self.is_running = True
        self.attempt_count = 0
        self.start_time = time.time()
        
        try:
            # Get client session
            client = self._get_client()
            
            self._emit_progress('started', '예약 시작...')
            
            # Main reservation loop (like original CLI)
            while self.is_running:
                try:
                    self.attempt_count += 1
                    
                    # Show progress with spinning animation
                    waiting_chars = ["|", "/", "-", "\\"]
                    char = waiting_chars[self.attempt_count % 4]
                    self._emit_progress(
                        'searching', 
                        f'예약 대기 중... {char}',
                        waiting_char=char
                    )
                    
                    # Search for trains with current parameters
                    if self.rail_type == "SRT":
                        trains = client.search_train(**search_params)
                    else:  # KTX
                        trains = client.search_train(**search_params)
                    
                    # Check each selected train for availability
                    for train_idx in selected_trains:
                        if train_idx < len(trains):
                            train = trains[train_idx]
                            
                            if self._is_seat_available(train, seat_type):
                                # Attempt reservation
                                self._emit_progress('reserving', f'예약 시도 중: {train.train_name} {train.train_number}')
                                
                                # Create passenger objects based on rail type
                                reservation_passengers = self._create_passengers(passengers)
                                
                                # Make reservation with detailed error handling
                                print(f"DEBUG: About to make reservation - rail_type={self.rail_type}, seat_type={seat_type}")
                                print(f"DEBUG: train={train}, passengers={reservation_passengers}")
                                
                                if self.rail_type == "SRT":
                                    from srtgo.srt import SeatType
                                    print(f"DEBUG: Available SeatType options: {dir(SeatType)}")
                                    
                                    # Safe seat option retrieval
                                    if hasattr(SeatType, seat_type):
                                        seat_option = getattr(SeatType, seat_type)
                                        print(f"DEBUG: Using seat_option={seat_option}")
                                    else:
                                        print(f"ERROR: Invalid seat_type '{seat_type}', using GENERAL_FIRST as fallback")
                                        seat_option = SeatType.GENERAL_FIRST
                                    
                                    print("DEBUG: Calling client.reserve() for SRT...")
                                    reservation = client.reserve(train, passengers=reservation_passengers, option=seat_option)
                                    print(f"DEBUG: SRT reservation result: {reservation}")
                                    
                                else:  # KTX
                                    from srtgo.ktx import ReserveOption
                                    print(f"DEBUG: Available ReserveOption options: {dir(ReserveOption)}")
                                    
                                    # Safe reserve option retrieval
                                    if hasattr(ReserveOption, seat_type):
                                        reserve_option = getattr(ReserveOption, seat_type)
                                        print(f"DEBUG: Using reserve_option={reserve_option}")
                                    else:
                                        print(f"ERROR: Invalid seat_type '{seat_type}', using GENERAL_FIRST as fallback")
                                        reserve_option = ReserveOption.GENERAL_FIRST
                                    
                                    print("DEBUG: Calling client.reserve() for KTX...")
                                    reservation = client.reserve(train, passengers=reservation_passengers, option=reserve_option)
                                    print(f"DEBUG: KTX reservation result: {reservation}")
                                
                                # Success!
                                result = {
                                    'success': True,
                                    'reservation': reservation,
                                    'train': train,
                                    'message': f'예약 성공! {train.train_name} {train.train_number}'
                                }
                                
                                self._emit_progress('success', result['message'], reservation=reservation)
                                
                                # Auto-payment if enabled
                                if auto_payment and not reservation.is_waiting:
                                    try:
                                        # Implement payment logic here
                                        self._emit_progress('paying', '자동 결제 중...')
                                        # payment_success = self._process_payment(client, reservation)
                                        # if payment_success:
                                        #     result['payment_success'] = True
                                        #     self._emit_progress('paid', '결제 완료!')
                                    except Exception as pay_ex:
                                        self._emit_progress('warning', f'결제 실패: {str(pay_ex)}')
                                
                                self.is_running = False
                                return result
                    
                    # No available trains found, sleep and retry
                    self._sleep_gamma()
                    
                except Exception as ex:
                    # Handle errors with sophisticated logic
                    if not self._handle_reservation_error(ex, debug):
                        # Stop reservation on critical error
                        self.is_running = False
                        return {
                            'success': False,
                            'error': str(ex),
                            'message': f'예약 실패: {str(ex)}'
                        }
                    
                    # Continue retrying after sleep
                    self._sleep_gamma()
                    
        except Exception as ex:
            self.is_running = False
            self._emit_progress('error', f'예약 중 오류: {str(ex)}')
            return {
                'success': False, 
                'error': str(ex),
                'message': f'예약 실패: {str(ex)}'
            }
        
        # Should not reach here
        self.is_running = False
        return {'success': False, 'message': '예약이 중단되었습니다'}
    
    def _create_passengers(self, passengers) -> List[Any]:
        """Create passenger objects based on rail type
        Args:
            passengers: Either List[Dict[str, Any]] or List[str]
        """
        passenger_objects = []
        
        print(f"DEBUG: _create_passengers called with: {passengers}")
        print(f"DEBUG: passengers type: {type(passengers)}")
        
        if self.rail_type == "SRT":
            from srtgo.srt import Adult, Child, Senior, Disability1To3, Disability4To6
            passenger_classes = {
                'adult': Adult,
                'child': Child, 
                'senior': Senior,
                'disability1to3': Disability1To3,
                'disability4to6': Disability4To6
            }
        else:  # KTX
            from srtgo.ktx import AdultPassenger, ChildPassenger, SeniorPassenger, Disability1To3Passenger, Disability4To6Passenger
            passenger_classes = {
                'adult': AdultPassenger,
                'child': ChildPassenger,
                'senior': SeniorPassenger, 
                'disability1to3': Disability1To3Passenger,
                'disability4to6': Disability4To6Passenger
            }
        
        # Handle both string list and dict list formats
        if passengers and isinstance(passengers[0], str):
            # Handle string list format: ['Adult', 'Adult', 'Child']
            print("DEBUG: Processing string list format")
            passenger_counts = {}
            for passenger_str in passengers:
                key = passenger_str.lower()
                passenger_counts[key] = passenger_counts.get(key, 0) + 1
            
            print(f"DEBUG: Passenger counts: {passenger_counts}")
            
            for passenger_type, count in passenger_counts.items():
                if count > 0 and passenger_type in passenger_classes:
                    print(f"DEBUG: Creating {count} x {passenger_type}")
                    passenger_objects.append(passenger_classes[passenger_type](count))
                    
        else:
            # Handle dict list format: [{'type': 'adult', 'count': 2}]
            print("DEBUG: Processing dict list format")
            for passenger in passengers:
                passenger_type = passenger.get('type', 'adult')
                count = passenger.get('count', 1)
                if count > 0 and passenger_type in passenger_classes:
                    print(f"DEBUG: Creating {count} x {passenger_type}")
                    passenger_objects.append(passenger_classes[passenger_type](count))
        
        print(f"DEBUG: Created passenger objects: {passenger_objects}")
        return passenger_objects
    
    def stop_reservation(self):
        """Stop the reservation process"""
        self.is_running = False
        self._emit_progress('stopped', '예약이 중단되었습니다')