import functools
import secrets

from flask import Flask, request, jsonify
import keyring

from srtgo.core import (
    set_login_credentials,
    reserve_train,
    search_trains,
    get_reservations,
    cancel_reservation,
    set_card_info,
    set_telegram_info,
    set_station_info,
    set_option_settings,
)

app = Flask(__name__)

TOKEN_SERVICE = "webapp"
TOKEN_NAME = "token"


def _ensure_token() -> str:
    token = keyring.get_password(TOKEN_SERVICE, TOKEN_NAME)
    if token is None:
        token = secrets.token_hex(16)
        keyring.set_password(TOKEN_SERVICE, TOKEN_NAME, token)
        print("Generated auth token:", token)
    return token


AUTH_TOKEN = _ensure_token()


def require_auth(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if request.headers.get("X-Auth-Token") != AUTH_TOKEN:
            return jsonify({"error": "unauthorized"}), 401
        return func(*args, **kwargs)

    return wrapper


@app.post("/login")
@require_auth
def login_route():
    try:
        data = request.get_json(force=True)
        rail_type = data.get("rail_type", "SRT")
        success = set_login_credentials(rail_type, data["id"], data["password"])
        if success:
            return jsonify({"message": "ok"})
        return jsonify({"message": "Invalid credentials"}), 400
    except KeyError as exc:
        return jsonify({"message": f"Missing field: {exc.args[0]}"}), 400
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500


@app.get("/reserve")
@require_auth
def search_route():
    try:
        rail_type = request.args.get("rail_type", "SRT")
        dep = request.args["departure"]
        arr = request.args["arrival"]
        date = request.args["date"]
        time = request.args.get("time", "000000")
        trains = search_trains(rail_type, dep, arr, date, time)
        return jsonify([str(t) for t in trains])
    except KeyError as exc:
        return jsonify({"message": f"Missing parameter: {exc.args[0]}"}), 400
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500


@app.post("/reserve")
@require_auth
def reserve_route():
    try:
        data = request.get_json(force=True)
        rail_type = data.get("rail_type", "SRT")
        reservation = reserve_train(
            rail_type,
            data["departure"],
            data["arrival"],
            data["date"],
            data.get("time", "000000"),
            data.get("passengers"),
            data.get("seat_type"),
            data.get("pay", False),
        )
        return jsonify({"reservation": str(reservation)})
    except KeyError as exc:
        return jsonify({"message": f"Missing field: {exc.args[0]}"}), 400
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500


@app.get("/reservations")
@require_auth
def list_reservations():
    try:
        rail_type = request.args.get("rail_type", "SRT")
        res = get_reservations(rail_type)
        return jsonify([str(r) for r in res])
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500


@app.delete("/reservations/<pnr>")
@require_auth
def cancel(pnr):
    try:
        rail_type = request.args.get("rail_type", "SRT")
        res_list = get_reservations(rail_type)
        for r in res_list:
            if getattr(r, "reservation_number", None) == pnr:
                cancel_reservation(rail_type, r)
                return jsonify({"message": "ok"})
        return jsonify({"message": "not_found"}), 404
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500


@app.post("/settings/card")
@require_auth
def card_settings():
    try:
        data = request.get_json(force=True)
        set_card_info(data["number"], data["password"], data["birthday"], data["expire"])
        return jsonify({"message": "ok"})
    except KeyError as exc:
        return jsonify({"message": f"Missing field: {exc.args[0]}"}), 400
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500


@app.post("/settings/telegram")
@require_auth
def telegram_settings():
    try:
        data = request.get_json(force=True)
        set_telegram_info(data["token"], data["chat_id"])
        return jsonify({"message": "ok"})
    except KeyError as exc:
        return jsonify({"message": f"Missing field: {exc.args[0]}"}), 400
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500


@app.post("/settings/stations")
@require_auth
def station_settings():
    try:
        data = request.get_json(force=True)
        rail_type = data.get("rail_type", "SRT")
        set_station_info(rail_type, data.get("stations", []))
        return jsonify({"message": "ok"})
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500


@app.post("/settings/options")
@require_auth
def option_settings():
    try:
        data = request.get_json(force=True)
        set_option_settings(data.get("options", []))
        return jsonify({"message": "ok"})
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500


@app.post("/token")
@require_auth
def reset_token():
    global AUTH_TOKEN
    AUTH_TOKEN = secrets.token_hex(16)
    keyring.set_password(TOKEN_SERVICE, TOKEN_NAME, AUTH_TOKEN)
    return jsonify({"token": AUTH_TOKEN})


def main():
    app.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
