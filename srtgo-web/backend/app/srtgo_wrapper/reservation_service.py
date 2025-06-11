import sys
import os
import time
from datetime import datetime
from typing import Dict, Any, Callable, Optional
from random import gammavariate

# Add original srtgo module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../srtgo'))

try:
    from srtgo.srt import SRT, SRTError, SeatType, Adult, Child, Senior, Disability1To3, Disability4To6
    from srtgo.ktx import Korail, KorailError, ReserveOption, TrainType, AdultPassenger, ChildPassenger, SeniorPassenger, Disability1To3Passenger, Disability4To6Passenger
    from curl_cffi.requests.exceptions import ConnectionError
    from json.decoder import JSONDecodeError
except ImportError as e:
    print(f"Warning: Could not import srtgo modules: {e}")
    # Create mock classes for development
    class SRT:
        def __init__(self, *args, **kwargs): pass
    class Korail:
        def __init__(self, *args, **kwargs): pass


class ReservationService:
    """Service class to wrap original srtgo functionality for web use"""
    
    def __init__(self):
        self.RESERVE_INTERVAL_SHAPE = 4
        self.RESERVE_INTERVAL_SCALE = 0.25
        self.RESERVE_INTERVAL_MIN = 0.25
        self.WAITING_BAR = ["|", "/", "-", "\\"]
    
    def start_reservation(
        self, 
        reservation: Any, 
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Start reservation process based on reservation data
        Returns: {"success": bool, "train_info": dict, "error": str}
        """
        try:
            # Initialize rail client
            rail_type = reservation.rail_type
            rail = self._login(reservation.user_id, rail_type)
            
            if not rail:
                return {"success": False, "error": "로그인 실패"}
            
            # Convert reservation data to search parameters
            params = self._build_search_params(reservation)
            
            # Get passenger classes
            passenger_classes = self._get_passenger_classes(rail_type)
            passengers = self._build_passengers(reservation.passengers, passenger_classes)
            
            # Start reservation loop
            i_try = 0
            start_time = time.time()
            
            while True:
                try:
                    i_try += 1
                    elapsed_time = time.time() - start_time
                    hours, remainder = divmod(int(elapsed_time), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    progress_msg = f"예매 대기 중... {self.WAITING_BAR[i_try & 3]} {i_try:4d} ({hours:02d}:{minutes:02d}:{seconds:02d})"
                    if progress_callback:
                        progress_callback(progress_msg, i_try)
                    
                    # Search for trains
                    trains = rail.search_train(**params)
                    
                    if not trains:
                        if progress_callback:
                            progress_callback("예약 가능한 열차가 없습니다", i_try)
                        self._sleep()
                        continue
                    
                    # Check selected trains for availability
                    for train_idx in reservation.selected_trains:
                        if train_idx < len(trains):
                            train = trains[train_idx]
                            if self._is_seat_available(train, reservation.seat_type, rail_type):
                                # Attempt reservation
                                try:
                                    reserved = rail.reserve(
                                        train, 
                                        passengers=passengers, 
                                        option=self._get_seat_option(reservation.seat_type, rail_type)
                                    )
                                    
                                    # Success!
                                    train_info = self._format_train_info(reserved)
                                    
                                    # Handle auto payment if enabled
                                    if reservation.auto_payment and hasattr(reserved, 'is_waiting') and not reserved.is_waiting:
                                        payment_success = self._pay_card(rail, reserved, reservation.user_id)
                                        if payment_success:
                                            train_info["payment_status"] = "completed"
                                    
                                    return {
                                        "success": True,
                                        "train_info": train_info,
                                        "message": "예매 성공!"
                                    }
                                    
                                except Exception as e:
                                    if progress_callback:
                                        progress_callback(f"예매 시도 실패: {str(e)}", i_try)
                    
                    self._sleep()
                    
                except (SRTError, KorailError) as ex:
                    if not self._handle_reservation_error(ex, rail, rail_type, progress_callback):
                        return {"success": False, "error": str(ex)}
                    self._sleep()
                    
                except (JSONDecodeError, ConnectionError) as ex:
                    if progress_callback:
                        progress_callback(f"연결 오류: {str(ex)}", i_try)
                    rail = self._login(reservation.user_id, rail_type)
                    self._sleep()
                    
                except Exception as ex:
                    return {"success": False, "error": f"예상치 못한 오류: {str(ex)}"}
                    
        except Exception as e:
            return {"success": False, "error": f"예매 초기화 실패: {str(e)}"}
    
    def _login(self, user_id: int, rail_type: str) -> Optional[Any]:
        """Login to rail system using stored credentials"""
        # TODO: Get credentials from user settings
        # For now, return mock login
        try:
            if rail_type == "SRT":
                return SRT("dummy", "dummy", verbose=False)
            else:
                return Korail("dummy", "dummy", verbose=False)
        except:
            return None
    
    def _build_search_params(self, reservation: Any) -> Dict[str, Any]:
        """Build search parameters from reservation data"""
        # Get passenger classes for search
        rail_type = reservation.rail_type
        passenger_classes = self._get_passenger_classes(rail_type)
        
        # Total passenger count for search
        total_count = sum(reservation.passengers.values())
        
        params = {
            "dep": reservation.departure_station,
            "arr": reservation.arrival_station, 
            "date": reservation.departure_date,
            "time": reservation.departure_time,
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
    
    def _pay_card(self, rail: Any, reservation: Any, user_id: int) -> bool:
        """Attempt automatic card payment"""
        # TODO: Get card info from user settings and implement payment
        return False
    
    def _handle_reservation_error(self, ex: Exception, rail: Any, rail_type: str, progress_callback: Optional[Callable] = None) -> bool:
        """Handle reservation errors and decide whether to continue"""
        msg = str(ex)
        
        # Errors that should stop reservation
        stop_errors = [
            "정상적인 경로로 접근 부탁드립니다",
            "로그인 후 사용하십시오"
        ]
        
        # Errors that should continue (normal flow)
        continue_errors = [
            "잔여석없음",
            "사용자가 많아 접속이 원활하지 않습니다", 
            "예약대기 접수가 마감되었습니다",
            "예약대기자한도수초과",
            "Sold out"
        ]
        
        if any(err in msg for err in stop_errors):
            if progress_callback:
                progress_callback(f"로그인 오류: {msg}", 0)
            return False
        
        if any(err in msg for err in continue_errors):
            if progress_callback:
                progress_callback(f"일시적 오류: {msg}", 0)
            return True
        
        # Unknown error - log and continue
        if progress_callback:
            progress_callback(f"알 수 없는 오류: {msg}", 0)
        return True
    
    def _sleep(self):
        """Sleep with gamma distribution interval"""
        time.sleep(
            gammavariate(self.RESERVE_INTERVAL_SHAPE, self.RESERVE_INTERVAL_SCALE)
            + self.RESERVE_INTERVAL_MIN
        )