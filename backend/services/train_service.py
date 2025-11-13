"""Service for interacting with train APIs (SRT/KTX)."""
import sys
import os

# Add parent directory to path to import existing srtgo module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from srtgo.srt import SRT, SRTError
from srtgo.ktx import Korail, KorailError
from typing import List, Dict, Any, Tuple


class TrainService:
    """Service for train operations using existing SRT/KTX libraries."""

    def __init__(self):
        """Initialize train service."""
        self.srt_client = None
        self.ktx_client = None

    async def login(self, train_type: str, user_id: str, password: str) -> Tuple[bool, str]:
        """
        Login to train service.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if train_type == "SRT":
                self.srt_client = SRT(user_id, password, auto_login=False)
                self.srt_client.login()
                return True, "SRT login successful"
            elif train_type == "KTX":
                self.ktx_client = Korail(user_id, password, auto_login=False)
                self.ktx_client.login()
                return True, "KTX login successful"
            else:
                return False, "Invalid train type"
        except (SRTError, KorailError) as e:
            return False, str(e)
        except Exception as e:
            return False, f"Login failed: {str(e)}"

    async def search_trains(
        self,
        train_type: str,
        departure: str,
        arrival: str,
        date: str,
        time: str,
        passengers: Dict[str, int]
    ) -> List[Any]:
        """
        Search for available trains.

        Args:
            train_type: 'SRT' or 'KTX'
            departure: Departure station name
            arrival: Arrival station name
            date: Date in YYYYMMDD format
            time: Time in HHMMSS format
            passengers: Dictionary of passenger counts

        Returns:
            List of train objects
        """
        try:
            if train_type == "SRT":
                if not self.srt_client:
                    raise ValueError("SRT client not initialized. Please login first.")

                # Convert passengers dict to SRT passenger objects
                passenger_list = []
                from srtgo.srt import Adult, Child, Senior, Disability1To3, Disability4To6

                for _ in range(passengers.get('adult', 1)):
                    passenger_list.append(Adult())
                for _ in range(passengers.get('child', 0)):
                    passenger_list.append(Child())
                for _ in range(passengers.get('senior', 0)):
                    passenger_list.append(Senior())
                for _ in range(passengers.get('disability1to3', 0)):
                    passenger_list.append(Disability1To3())
                for _ in range(passengers.get('disability4to6', 0)):
                    passenger_list.append(Disability4To6())

                trains = self.srt_client.search_train(
                    departure,
                    arrival,
                    date,
                    time,
                    passengers=passenger_list
                )
                return trains

            elif train_type == "KTX":
                if not self.ktx_client:
                    raise ValueError("KTX client not initialized. Please login first.")

                # Convert passengers dict to KTX passenger objects
                from srtgo.ktx import (
                    AdultPassenger,
                    ChildPassenger,
                    SeniorPassenger,
                    Disability1To3Passenger,
                    Disability4To6Passenger
                )

                passenger_list = []
                for _ in range(passengers.get('adult', 1)):
                    passenger_list.append(AdultPassenger())
                for _ in range(passengers.get('child', 0)):
                    passenger_list.append(ChildPassenger())
                for _ in range(passengers.get('senior', 0)):
                    passenger_list.append(SeniorPassenger())
                for _ in range(passengers.get('disability1to3', 0)):
                    passenger_list.append(Disability1To3Passenger())
                for _ in range(passengers.get('disability4to6', 0)):
                    passenger_list.append(Disability4To6Passenger())

                trains = self.ktx_client.search_train(
                    departure,
                    arrival,
                    date,
                    time,
                    passengers=passenger_list
                )
                return trains

            else:
                raise ValueError("Invalid train type")

        except (SRTError, KorailError) as e:
            raise ValueError(str(e))
        except Exception as e:
            raise ValueError(f"Search failed: {str(e)}")

    async def reserve_train(
        self,
        train_type: str,
        train: Any,
        passengers: Dict[str, int],
        seat_type: str = None
    ) -> Tuple[bool, Any, str]:
        """
        Reserve a train.

        Returns:
            Tuple of (success: bool, reservation: Any, message: str)
        """
        try:
            if train_type == "SRT":
                if not self.srt_client:
                    raise ValueError("SRT client not initialized. Please login first.")

                reservation = self.srt_client.reserve(train)
                return True, reservation, "Reservation successful"

            elif train_type == "KTX":
                if not self.ktx_client:
                    raise ValueError("KTX client not initialized. Please login first.")

                reservation = self.ktx_client.reserve(train)
                return True, reservation, "Reservation successful"

            else:
                return False, None, "Invalid train type"

        except (SRTError, KorailError) as e:
            return False, None, str(e)
        except Exception as e:
            return False, None, f"Reservation failed: {str(e)}"

    async def get_reservations(self, train_type: str) -> List[Any]:
        """Get all reservations for the user."""
        try:
            if train_type == "SRT":
                if not self.srt_client:
                    raise ValueError("SRT client not initialized.")
                return self.srt_client.get_reservations()

            elif train_type == "KTX":
                if not self.ktx_client:
                    raise ValueError("KTX client not initialized.")
                return self.ktx_client.reservations()

            else:
                raise ValueError("Invalid train type")

        except (SRTError, KorailError) as e:
            raise ValueError(str(e))
        except Exception as e:
            raise ValueError(f"Failed to get reservations: {str(e)}")

    def logout(self, train_type: str):
        """Logout from train service."""
        if train_type == "SRT":
            self.srt_client = None
        elif train_type == "KTX":
            self.ktx_client = None
