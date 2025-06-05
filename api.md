# SRTgo Web API

This document describes the REST API exposed by `srtgo-web`. All requests must
include the `X-Auth-Token` header obtained via `keyring get webapp token` when
starting the server for the first time.

## /login (POST)
Set login credentials.

### Body Parameters
- `id` (string, required): account ID.
- `password` (string, required): account password.
- `rail_type` (string, optional): `SRT` (default) or `KTX`.

### Sample Request
```bash
curl -X POST http://localhost:8000/login \
  -H "X-Auth-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id":"user","password":"pass"}'
```

### Sample Response
```json
{"message": "ok"}
```

## /reserve
### GET
Search for trains.

#### Query Parameters
- `departure` (string, required)
- `arrival` (string, required)
- `date` (string, required, format `YYYYMMDD`)
- `time` (string, optional, `HHMMSS`, default `000000`)
- `rail_type` (string, optional, default `SRT`)
- `include_no_seats` (boolean, optional)
- `include_waiting_list` (boolean, optional)

### Sample Response
```json
[
  {"train_number": "333", "dep_time": "1250", "arr_time": "1434"}
]
```

### POST
Make a reservation.

#### Body Parameters
- `departure`, `arrival`, `date`, `time` (same as above)
- `passengers` (list, optional)
- `seat_type` (string, optional)
- `pay` (boolean, optional): immediately pay with saved card
- `rail_type` (string, optional, default `SRT`)

### Sample Response
```json
{"reservation": {"reservation_number": "123456"}}
```

## /reservations
### GET
List existing reservations.

#### Query Parameters
- `rail_type` (string, optional, default `SRT`)

### DELETE `/reservations/<pnr>`
Cancel a reservation by PNR.

## /settings/*
Each settings endpoint accepts JSON data and returns `{"message": "ok"}` on
success.

- `/settings/card`: `number`, `password`, `birthday`, `expire`
- `/settings/telegram`: `token`, `chat_id`
- `/settings/stations`: `rail_type` (optional) and `stations` (list)
- `/settings/options`: `options` (list)

## Regenerating the token
`POST /token` with the current `X-Auth-Token` header returns a new token.

## Starting the Server
Install the `web` extras and run `srtgo-web`:
```bash
pip install .[web]
srtgo-web
```
The API will be served on port `8000`. Swagger documentation is available at
`/apidocs` when `flasgger` is installed.
