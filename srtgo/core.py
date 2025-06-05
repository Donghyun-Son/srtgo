import keyring
from .srtgo import login as _cli_login, pay_card as _cli_pay_card
from .srt import SRT, SeatType
from .ktx import Korail, ReserveOption, AdultPassenger, ChildPassenger, SeniorPassenger, Disability1To3Passenger, Disability4To6Passenger

__all__ = [
    "login", "set_login_credentials", "search_trains", "reserve_train",
    "get_reservations", "cancel_reservation",
    "set_card_info", "set_telegram_info", "set_station_info", "set_option_settings",
]


def set_login_credentials(rail_type: str, user_id: str, password: str, debug: bool = False) -> bool:
    """Store user login credentials after verifying."""
    try:
        if rail_type == "SRT":
            SRT(user_id, password, verbose=debug)
        else:
            Korail(user_id, password, verbose=debug)
    except Exception:
        return False

    keyring.set_password(rail_type, "id", user_id)
    keyring.set_password(rail_type, "pass", password)
    keyring.set_password(rail_type, "ok", "1")
    return True


def login(rail_type: str = "SRT", debug: bool = False):
    """Login using stored credentials."""
    return _cli_login(rail_type=rail_type, debug=debug)


def search_trains(rail_type: str, departure: str, arrival: str, date: str, time: str):
    rail = login(rail_type)
    return rail.search_train(departure, arrival, date, time)


def _build_passengers(rail_type: str, counts: dict):
    if rail_type == "SRT":
        from .srt import Adult, Child, Senior, Disability1To3, Disability4To6
        cls_map = {
            "adult": Adult,
            "child": Child,
            "senior": Senior,
            "disability1to3": Disability1To3,
            "disability4to6": Disability4To6,
        }
    else:
        cls_map = {
            "adult": AdultPassenger,
            "child": ChildPassenger,
            "senior": SeniorPassenger,
            "disability1to3": Disability1To3Passenger,
            "disability4to6": Disability4To6Passenger,
        }
    passengers = []
    for key, cls in cls_map.items():
        cnt = int(counts.get(key, 0))
        if cnt:
            passengers.append(cls(cnt))
    return passengers


def reserve_train(
    rail_type: str,
    departure: str,
    arrival: str,
    date: str,
    time: str,
    passengers: dict | None = None,
    seat_type: str | None = None,
    pay: bool = False,
):
    rail = login(rail_type)
    trains = rail.search_train(departure, arrival, date, time)
    if not trains:
        raise RuntimeError("No trains found")
    train = trains[0]
    passengers = _build_passengers(rail_type, passengers or {"adult": 1})
    if rail_type == "SRT":
        option = SeatType[seat_type] if seat_type else SeatType.GENERAL_FIRST
    else:
        option = ReserveOption[seat_type] if seat_type else ReserveOption.GENERAL_FIRST
    reservation = rail.reserve(train, passengers=passengers, option=option)
    if pay and not getattr(reservation, "is_waiting", False):
        _cli_pay_card(rail, reservation)
    return reservation


def get_reservations(rail_type: str):
    rail = login(rail_type)
    if rail_type == "SRT":
        return rail.get_reservations()
    return rail.reservations()


def cancel_reservation(rail_type: str, reservation):
    rail = login(rail_type)
    if rail_type == "SRT":
        rail.cancel(reservation)
    else:
        rail.cancel(reservation)


# Settings helpers

def set_card_info(number: str, password: str, birthday: str, expire: str):
    keyring.set_password("card", "number", number)
    keyring.set_password("card", "password", password)
    keyring.set_password("card", "birthday", birthday)
    keyring.set_password("card", "expire", expire)
    keyring.set_password("card", "ok", "1")


def set_telegram_info(token: str, chat_id: str):
    keyring.set_password("telegram", "token", token)
    keyring.set_password("telegram", "chat_id", chat_id)
    keyring.set_password("telegram", "ok", "1")


def set_station_info(rail_type: str, stations: list[str]):
    keyring.set_password(rail_type, "station", ",".join(stations))


def set_option_settings(options: list[str]):
    keyring.set_password("SRT", "options", ",".join(options))
