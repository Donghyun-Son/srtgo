"""
SRTgo compatibility wrapper
원본 srtgo 코드를 수정하지 않고 curl_cffi 호환성 문제를 해결하는 helper
"""
import sys
import os
from typing import Optional

# srtgo 모듈 경로를 Python path에 추가
srtgo_path = os.path.join(os.path.dirname(__file__), '../../')
if os.path.exists(os.path.join(srtgo_path, 'srtgo')):
    sys.path.insert(0, srtgo_path)
else:
    # Docker 환경에서는 /app에 있을 수 있음
    sys.path.insert(0, '/app')

        
def safe_srt_login(username: str, password: str) -> bool:
    """안전한 SRT 로그인 테스트"""
    try:
        # srtgo 패치 적용
        from .srtgo_patch import patch_srtgo_modules
        patch_srtgo_modules()
        
        # srtgo 모듈 import
        from srtgo.srt import SRT
        
        # SRT 인스턴스 생성 및 로그인 테스트
        srt = SRT(username, password, auto_login=False)
        result = srt.login()
        print(f"SRT login result for {username}: {result}")
        return result
        
    except Exception as e:
        print(f"SRT login error for {username}: {e}")
        import traceback
        traceback.print_exc()
        return False

def safe_ktx_login(username: str, password: str) -> bool:
    """안전한 KTX 로그인 테스트"""
    try:
        # srtgo 패치 적용
        from .srtgo_patch import patch_srtgo_modules
        patch_srtgo_modules()
        
        # srtgo 모듈 import
        from srtgo.ktx import Korail
        
        # KTX 인스턴스 생성 및 로그인 테스트
        ktx = Korail(username, password, auto_login=False)
        result = ktx.login()
        print(f"KTX login result for {username}: {result}")
        return result
        
    except Exception as e:
        print(f"KTX login error for {username}: {e}")
        import traceback
        traceback.print_exc()
        return False

def authenticate_external(username: str, password: str, rail_type: str) -> bool:
    """외부 SRT/KTX 시스템과 인증"""
    from app.core.error_handler import handle_srt_error
    
    try:
        rail_type = rail_type.upper()
        
        if rail_type == "SRT":
            return safe_srt_login(username, password)
        elif rail_type == "KTX":
            return safe_ktx_login(username, password)
        else:
            print(f"Unsupported rail type: {rail_type}")
            return False
    except Exception as e:
        handle_srt_error(str(e))
        return False


def test_srt_login(login_id: str, password: str):
    """SRT 로그인 테스트 (API 용)"""
    try:
        success = safe_srt_login(login_id, password)
        if success:
            return True, "SRT 로그인 성공"
        else:
            return False, "SRT 로그인 실패: 아이디 또는 비밀번호가 잘못되었습니다"
    except Exception as e:
        return False, f"SRT 로그인 오류: {str(e)}"


def test_ktx_login(login_id: str, password: str):
    """KTX 로그인 테스트 (API 용)"""
    try:
        success = safe_ktx_login(login_id, password)
        if success:
            return True, "KTX 로그인 성공"
        else:
            return False, "KTX 로그인 실패: 아이디 또는 비밀번호가 잘못되었습니다"
    except Exception as e:
        return False, f"KTX 로그인 오류: {str(e)}"


def test_telegram(token: str, chat_id: str):
    """텔레그램 테스트 메시지 전송"""
    try:
        from app.services.telegram_service import TelegramService
        from app.core.database import engine
        from sqlmodel import Session
        import asyncio
        
        with Session(engine) as session:
            telegram_service = TelegramService(session)
            result = asyncio.run(telegram_service.send_test_message(token, chat_id))
            return result['success'], result['message']
    except Exception as e:
        return False, f"텔레그램 연결 오류: {str(e)}"


def search_trains(rail_type: str, login_id: str, password: str, 
                 departure: str, arrival: str, date: str, time: str,
                 available_only: bool = True, include_no_seats: bool = False):
    """열차 검색 - 세션 매니저 사용"""
    try:
        # Import session manager
        from app.services.redis_session_manager import redis_session_manager as session_manager
        
        # srtgo 패치 적용
        from .srtgo_patch import patch_srtgo_modules
        patch_srtgo_modules()
        
        rail_type = rail_type.upper()
        user_key = f"{rail_type.lower()}_{login_id}"
        

        # Try to get existing session
        client = session_manager.get_session(user_key)
        
        if not client:
            # Create new session if needed
            client = session_manager.create_session(user_key, rail_type, login_id, password)
            if not client:
                raise Exception("Failed to create session")
        
        # Search trains with options
        if rail_type == "SRT":
            trains = client.search_train(dep=departure, arr=arrival, date=date, time=time, 
                                       available_only=available_only)
        elif rail_type == "KTX":
            # KTX has different parameter name
            trains = client.search_train(dep=departure, arr=arrival, date=date, time=time,
                                       include_no_seats=include_no_seats)
        else:
            raise ValueError(f"Unsupported rail type: {rail_type}")
        
        # 열차 정보를 딕셔너리로 변환
        train_list = []
        for train in trains:
            # 좌석 상태 정보 추출
            general_state = getattr(train, "general_seat_state", "")
            special_state = getattr(train, "special_seat_state", "")
            reserve_possible = getattr(train, "reserve_possible", False)
            
            # 좌석 가용성 판단 (예약가능, 예약대기, 매진 모두 포함)
            general_available = general_state == "예약가능"
            special_available = special_state == "예약가능"
            waiting_available = reserve_possible or general_state == "예약대기" or special_state == "예약대기"
            
            train_dict = {
                "train_name": getattr(train, "train_name", ""),
                "train_no": getattr(train, "train_number", ""),
                "departure_time": getattr(train, "dep_time", ""),
                "arrival_time": getattr(train, "arr_time", ""),
                "departure_station": getattr(train, "dep_station_name", ""),
                "arrival_station": getattr(train, "arr_station_name", ""),
                "general_seat_available": general_available,
                "special_seat_available": special_available,
                "waiting_available": waiting_available,
                "reservation_possible": reserve_possible,
                "general_seat_state": general_state,
                "special_seat_state": special_state,
                # 예약 가능 여부 (예약가능 + 예약대기 포함)
                "bookable": general_available or special_available or waiting_available,
                # 완전 매진 여부
                "sold_out": not (general_available or special_available or waiting_available),
            }
            train_list.append(train_dict)
        
        return True, train_list
    except Exception as e:
        from app.core.error_handler import handle_srt_error
        try:
            handle_srt_error(str(e))
        except Exception as handled_error:
            # Re-raise the handled error to be caught by FastAPI exception handler
            raise handled_error
        return False, f"열차 검색 오류: {str(e)}"