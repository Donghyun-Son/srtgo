"""Service for interacting with train APIs (SRT/KTX)."""
import sys
import os

# Add parent directory to path to import existing srtgo module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from srtgo.srt import SRT, SRTError, SeatType
from srtgo.ktx import Korail, KorailError, ReserveOption
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
                    passengers=passenger_list,
                    available_only=False  # Include unavailable trains for standby (same as CLI)
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
                    passengers=passenger_list,
                    include_no_seats=True  # Include trains without seats for waiting list (same as CLI)
                )
                return trains

            else:
                raise ValueError("Invalid train type")

        except (SRTError, KorailError) as e:
            raise ValueError(str(e))
        except Exception as e:
            raise ValueError(f"Search failed: {str(e)}")

    def is_seat_available(self, train: Any, train_type: str, seat_type: str = None) -> bool:
        """
        Check if seats are available for a train (same as CLI _is_seat_available).

        Args:
            train: Train object
            train_type: 'SRT' or 'KTX'
            seat_type: Seat type preference (e.g., 'general_only', 'special_only', 'general_first', 'special_first')

        Returns:
            True if seats are available (including standby), False otherwise
        """
        try:
            if train_type == "SRT":
                # Check regular seats first
                if not train.seat_available():
                    # If no regular seats, check standby availability
                    return train.reserve_standby_available()

                # If seats available, check by preference
                if not seat_type or seat_type == "general_first":
                    return train.seat_available()
                elif seat_type == "general_only":
                    return train.general_seat_available()
                elif seat_type == "special_first":
                    return train.seat_available()
                elif seat_type == "special_only":
                    return train.special_seat_available()
                else:
                    return train.seat_available()

            else:  # KTX
                # Check regular seats first
                if not train.has_seat():
                    # If no regular seats, check waiting list
                    return train.has_waiting_list()

                # If seats available, check by preference
                if not seat_type or seat_type == "general_first":
                    return train.has_seat()
                elif seat_type == "general_only":
                    return train.has_general_seat()
                elif seat_type == "special_first":
                    return train.has_seat()
                elif seat_type == "special_only":
                    return train.has_special_seat()
                else:
                    return train.has_seat()

        except Exception as e:
            print(f"Error checking seat availability: {e}")
            return False

    async def reserve_train(
        self,
        train_type: str,
        train: Any,
        passengers: Dict[str, int],
        seat_type: str = None
    ) -> Tuple[bool, Any, str]:
        """
        Reserve a train with seat type preference (same as CLI).

        Returns:
            Tuple of (success: bool, reservation: Any, message: str)
        """
        try:
            if train_type == "SRT":
                if not self.srt_client:
                    raise ValueError("SRT client not initialized. Please login first.")

                # Convert passengers dict to SRT passenger objects (same as CLI)
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

                # Map seat type string to SeatType enum
                option = SeatType.GENERAL_FIRST  # default
                if seat_type == "general_only":
                    option = SeatType.GENERAL_ONLY
                elif seat_type == "special_only":
                    option = SeatType.SPECIAL_ONLY
                elif seat_type == "special_first":
                    option = SeatType.SPECIAL_FIRST

                # Reserve with passengers (same as CLI: rail.reserve(train, passengers=passengers, option=option))
                reservation = self.srt_client.reserve(train, passengers=passenger_list, option=option)

                # If standby reservation with phone number, set options (same as CLI)
                if hasattr(reservation, 'is_waiting') and reservation.is_waiting:
                    phone_number = self.srt_client.phone_number if hasattr(self.srt_client, 'phone_number') else None
                    if phone_number:
                        # Set standby options: SMS agreement and class change agreement
                        agree_class_change = (option == SeatType.SPECIAL_FIRST or option == SeatType.GENERAL_FIRST)
                        try:
                            self.srt_client.reserve_standby_option_settings(
                                reservation,
                                isAgreeSMS=True,
                                isAgreeClassChange=agree_class_change,
                                telNo=phone_number
                            )
                        except Exception as e:
                            print(f"Warning: Failed to set standby options: {e}")

                return True, reservation, str(reservation)

            elif train_type == "KTX":
                if not self.ktx_client:
                    raise ValueError("KTX client not initialized. Please login first.")

                # Convert passengers dict to KTX passenger objects (same as CLI)
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

                # Map seat type string to ReserveOption enum
                option = ReserveOption.GENERAL_FIRST  # default
                if seat_type == "general_only":
                    option = ReserveOption.GENERAL_ONLY
                elif seat_type == "special_only":
                    option = ReserveOption.SPECIAL_ONLY
                elif seat_type == "special_first":
                    option = ReserveOption.SPECIAL_FIRST

                # Reserve with passengers (same as CLI)
                reservation = self.ktx_client.reserve(train, passengers=passenger_list, option=option)
                return True, reservation, str(reservation)

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

    def clear(self, train_type: str):
        """Clear netfunnel cache for train service."""
        try:
            if train_type == "SRT" and self.srt_client:
                self.srt_client.clear()
            elif train_type == "KTX" and self.ktx_client:
                self.ktx_client.clear()
        except Exception:
            pass  # Ignore errors during clear

    async def pay_with_card(
        self,
        train_type: str,
        reservation: Any,
        card_number: str,
        card_password: str,
        birthday: str,
        expire_date: str
    ) -> Tuple[bool, str]:
        """
        Pay for a reservation with card (same as CLI pay_card).

        Args:
            train_type: 'SRT' or 'KTX'
            reservation: Reservation object
            card_number: Card number
            card_password: Card password (first 2 digits)
            birthday: Birthday (YYMMDD for personal, YYYYMMDD for business)
            expire_date: Card expiration date (YYMM)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Determine card type based on birthday length
            card_type = "J" if len(birthday) == 6 else "S"  # J: 개인, S: 법인

            if train_type == "SRT":
                if not self.srt_client:
                    raise ValueError("SRT client not initialized.")

                result = self.srt_client.pay_with_card(
                    reservation,
                    card_number,
                    card_password,
                    birthday,
                    expire_date,
                    0,  # installment months (0 = 일시불)
                    card_type
                )
                return result, "Payment successful"

            elif train_type == "KTX":
                if not self.ktx_client:
                    raise ValueError("KTX client not initialized.")

                result = self.ktx_client.pay_with_card(
                    reservation,
                    card_number,
                    card_password,
                    birthday,
                    expire_date,
                    0,  # installment months (0 = 일시불)
                    card_type
                )
                return result, "Payment successful"

            else:
                return False, "Invalid train type"

        except (SRTError, KorailError) as e:
            return False, f"Payment failed: {str(e)}"
        except Exception as e:
            return False, f"Payment failed: {str(e)}"

    def logout(self, train_type: str):
        """Logout from train service."""
        if train_type == "SRT":
            self.srt_client = None
        elif train_type == "KTX":
            self.ktx_client = None
