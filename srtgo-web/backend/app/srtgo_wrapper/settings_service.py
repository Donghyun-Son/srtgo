import sys
import os
from typing import Dict, List, Optional

# Add original srtgo module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../srtgo'))

try:
    from srtgo.srtgo import STATIONS, DEFAULT_STATIONS
except ImportError:
    # Fallback data if import fails
    STATIONS = {
        "SRT": ["수서", "동탄", "평택지제", "경주", "곡성", "공주", "광주송정", "구례구", "김천(구미)", "나주", "남원", "대전", "동대구", "마산", "목포", "밀양", "부산", "서대구", "순천", "여수EXPO", "여천", "오송", "울산(통도사)", "익산", "전주", "정읍", "진영", "진주", "창원", "창원중앙", "천안아산", "포항"],
        "KTX": ["서울", "용산", "영등포", "광명", "수원", "천안아산", "오송", "대전", "서대전", "김천구미", "동대구", "경주", "포항", "밀양", "구포", "부산", "울산(통도사)", "마산", "창원중앙", "경산", "논산", "익산", "정읍", "광주송정", "목포", "전주", "순천", "여수EXPO", "청량리", "강릉", "행신", "정동진"]
    }
    DEFAULT_STATIONS = {
        "SRT": ["수서", "대전", "동대구", "부산"],
        "KTX": ["서울", "대전", "동대구", "부산"]
    }


class SettingsService:
    """Service class for managing settings and station data"""
    
    @staticmethod
    def get_stations(rail_type: str) -> List[str]:
        """Get available stations for rail type"""
        return STATIONS.get(rail_type, [])
    
    @staticmethod
    def get_default_stations(rail_type: str) -> List[str]:
        """Get default stations for rail type"""
        return DEFAULT_STATIONS.get(rail_type, [])
    
    @staticmethod
    def get_all_stations() -> Dict[str, List[str]]:
        """Get all available stations"""
        return STATIONS
    
    @staticmethod
    def validate_station(station_name: str, rail_type: str) -> bool:
        """Validate if station exists for given rail type"""
        return station_name in STATIONS.get(rail_type, [])
    
    @staticmethod
    def get_passenger_types() -> List[Dict[str, str]]:
        """Get available passenger types"""
        return [
            {"key": "adult", "label": "성인/청소년"},
            {"key": "child", "label": "어린이"},
            {"key": "senior", "label": "경로우대"},
            {"key": "disability1to3", "label": "1~3급 장애인"},
            {"key": "disability4to6", "label": "4~6급 장애인"},
        ]
    
    @staticmethod
    def get_seat_types() -> List[Dict[str, str]]:
        """Get available seat types"""
        return [
            {"key": "GENERAL_FIRST", "label": "일반실 우선"},
            {"key": "GENERAL_ONLY", "label": "일반실만"},
            {"key": "SPECIAL_FIRST", "label": "특실 우선"},
            {"key": "SPECIAL_ONLY", "label": "특실만"},
        ]
    
    @staticmethod
    def get_time_choices() -> List[Dict[str, str]]:
        """Get time choices for departure"""
        return [
            {"value": f"{h:02d}0000", "label": f"{h:02d}:00"}
            for h in range(24)
        ]