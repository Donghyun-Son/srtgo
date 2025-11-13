# SRTgo Web Backend

FastAPI backend for SRTgo web application.

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

Edit `.env`:
```env
SECRET_KEY=your-secret-key-here-change-in-production
DATABASE_URL=sqlite+aiosqlite:///./srtgo.db
```

Generate a secure SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Run the Server

```bash
# Development mode (with auto-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using Python
python main.py
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get token
- `GET /api/auth/me` - Get current user info

### Credentials
- `POST /api/credentials/train` - Add/update train credentials
- `GET /api/credentials/train` - Get train credentials
- `POST /api/credentials/card` - Add/update card credentials
- `GET /api/credentials/card` - Get card credentials
- `POST /api/credentials/telegram` - Add/update Telegram credentials
- `GET /api/credentials/telegram` - Get Telegram credentials

### Trains
- `POST /api/trains/search` - Search available trains
- `GET /api/trains/stations/{train_type}` - Get station list

### Reservations
- `POST /api/reservations` - Create new reservation
- `GET /api/reservations` - Get all reservations
- `GET /api/reservations/{id}` - Get specific reservation
- `POST /api/reservations/{id}/start-polling` - Start polling for availability
- `POST /api/reservations/{id}/stop-polling` - Stop polling
- `PATCH /api/reservations/{id}` - Update reservation
- `WS /api/reservations/ws/{id}` - WebSocket for real-time updates

## Database

The application uses SQLAlchemy with async support. By default, it uses SQLite for simplicity.

To use PostgreSQL:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/srtgo
```

## Security

- Passwords are hashed using bcrypt
- JWT tokens for authentication
- Sensitive credentials (train login, card info) are encrypted using AES
- CORS configured for allowed origins only

## Architecture

```
backend/
├── api/              # API route handlers
│   ├── auth.py       # Authentication endpoints
│   ├── credentials.py # Credential management
│   ├── trains.py     # Train search
│   └── reservations.py # Reservation management
├── core/             # Core functionality
│   ├── config.py     # Configuration
│   ├── security.py   # Authentication & encryption
│   └── dependencies.py # FastAPI dependencies
├── models/           # Database models
│   ├── database.py   # DB setup
│   ├── user.py       # User model
│   ├── credential.py # Credential models
│   └── reservation.py # Reservation model
├── schemas/          # Pydantic schemas
│   ├── user.py       # User schemas
│   ├── credential.py # Credential schemas
│   └── reservation.py # Reservation schemas
├── services/         # Business logic
│   ├── train_service.py # Train operations
│   └── reservation_service.py # Reservation & polling
└── main.py           # FastAPI app entry point
```

## Development

### Running Tests
```bash
pytest
```

### Database Migrations
```bash
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## Production Deployment

1. Use a production-grade database (PostgreSQL)
2. Set `DEBUG=False` in `.env`
3. Use a strong `SECRET_KEY`
4. Configure proper CORS origins
5. Use a production ASGI server:

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Notes

- For 1-5 concurrent users, the current architecture is sufficient
- Background polling is handled with asyncio tasks (lightweight)
- For larger scale, consider using Celery for background jobs
- WebSocket connections are kept alive for real-time updates
