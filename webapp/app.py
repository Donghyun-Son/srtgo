from flask import Flask, request, jsonify

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


@app.post("/login")
def login_route():
    data = request.get_json(force=True)
    rail_type = data.get("rail_type", "SRT")
    if set_login_credentials(rail_type, data["id"], data["password"]):
        return jsonify({"status": "ok"})
    return jsonify({"status": "fail"}), 400


@app.get("/reserve")
def search_route():
    rail_type = request.args.get("rail_type", "SRT")
    dep = request.args["departure"]
    arr = request.args["arrival"]
    date = request.args["date"]
    time = request.args.get("time", "000000")
    trains = search_trains(rail_type, dep, arr, date, time)
    return jsonify([getattr(t, "to_dict", lambda: t.__dict__)() for t in trains])


@app.post("/reserve")
def reserve_route():
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
    return jsonify({"reservation": getattr(reservation, "to_dict", lambda: reservation.__dict__)()})


@app.get("/reservations")
def list_reservations():
    rail_type = request.args.get("rail_type", "SRT")
    res = get_reservations(rail_type)
    return jsonify([getattr(r, "to_dict", lambda: r.__dict__)() for r in res])


@app.delete("/reservations/<pnr>")
def cancel(pnr):
    rail_type = request.args.get("rail_type", "SRT")
    res_list = get_reservations(rail_type)
    for r in res_list:
        if getattr(r, "reservation_number", None) == pnr:
            cancel_reservation(rail_type, r)
            return jsonify({"status": "ok"})
    return jsonify({"status": "not_found"}), 404


@app.post("/settings/card")
def card_settings():
    data = request.get_json(force=True)
    set_card_info(data["number"], data["password"], data["birthday"], data["expire"])
    return jsonify({"status": "ok"})


@app.post("/settings/telegram")
def telegram_settings():
    data = request.get_json(force=True)
    set_telegram_info(data["token"], data["chat_id"])
    return jsonify({"status": "ok"})


@app.post("/settings/stations")
def station_settings():
    data = request.get_json(force=True)
    rail_type = data.get("rail_type", "SRT")
    set_station_info(rail_type, data.get("stations", []))
    return jsonify({"status": "ok"})


@app.post("/settings/options")
def option_settings():
    data = request.get_json(force=True)
    set_option_settings(data.get("options", []))
    return jsonify({"status": "ok"})


def main():
    app.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
