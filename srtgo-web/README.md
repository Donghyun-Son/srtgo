# SRTgo Web UI

Web-based interface for SRTgo Korean train reservation system.

## Project Structure

```
srtgo-web/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/       # API routes
│   │   ├── core/      # Core settings
│   │   ├── services/  # Business logic
│   │   ├── models/    # Data models
│   │   ├── tasks/     # Celery background tasks
│   │   └── srtgo_wrapper/  # Original srtgo module wrapper
│   └── tests/
├── frontend/          # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── utils/
│   └── public/
└── docker-compose.yml
```

## Development

### Prerequisites
- Docker & Docker Compose
- Python 3.10+
- Node.js 18+

### Quick Start
```bash
# Start all services
docker-compose up -d

# Backend only (development)
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend only (development)
cd frontend
npm install
npm start
```

## Features
- Web-based train reservation interface
- Real-time reservation monitoring
- Background reservation tasks
- Mobile-responsive design
- Multi-user support