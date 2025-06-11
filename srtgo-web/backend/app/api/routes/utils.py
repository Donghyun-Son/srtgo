from typing import List
from fastapi import APIRouter
from app.srtgo_wrapper.settings_service import SettingsService

router = APIRouter()


@router.get("/stations", response_model=List[str])
def get_stations(rail_type: str = None):
    """Get available stations"""
    if rail_type:
        return SettingsService.get_stations(rail_type)
    else:
        return SettingsService.get_all_stations()


@router.get("/passenger-types")
def get_passenger_types():
    """Get available passenger types"""
    return SettingsService.get_passenger_types()


@router.get("/seat-types")
def get_seat_types():
    """Get available seat types"""
    return SettingsService.get_seat_types()


@router.get("/time-choices")
def get_time_choices():
    """Get time choices for departure"""
    return SettingsService.get_time_choices()


@router.post("/search-trains")
def search_trains(params: dict):
    """Search for available trains"""
    # This would normally call the srtgo search functionality
    # For now, return mock data
    return {
        "trains": [],
        "message": "Train search functionality will be implemented with actual srtgo integration"
    }