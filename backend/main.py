"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path
from sqlalchemy import select

from backend.core.config import settings
from backend.models.database import init_db, AsyncSessionLocal
from backend.models.reservation import Reservation, ReservationStatus
from backend.services.reservation_service import reservation_service
from backend.api import (
    auth_router,
    credentials_router,
    trains_router,
    reservations_router,
)


async def resume_polling_tasks():
    """Resume polling for reservations that were searching when server stopped."""
    try:
        async with AsyncSessionLocal() as db:
            # Find all reservations in SEARCHING status
            result = await db.execute(
                select(Reservation).where(Reservation.status == ReservationStatus.SEARCHING)
            )
            searching_reservations = result.scalars().all()

            if searching_reservations:
                print(f"Found {len(searching_reservations)} interrupted polling tasks. Resuming...")
                for reservation in searching_reservations:
                    # Resume polling for each reservation
                    reservation_service.start_polling(reservation.id, db)
                    print(f"  - Resumed polling for reservation #{reservation.id}")
            else:
                print("No interrupted polling tasks found.")
    except Exception as e:
        print(f"Error resuming polling tasks: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    print("Initializing database...")
    await init_db()
    print("Database initialized!")

    # Resume interrupted polling tasks
    await resume_polling_tasks()

    yield
    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(credentials_router)
app.include_router(trains_router)
app.include_router(reservations_router)


# Serve static files (frontend)
# Check if frontend/dist directory exists
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    # Mount static files
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        """Serve frontend index.html."""
        return FileResponse(str(frontend_dist / "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend_routes(full_path: str):
        """Serve frontend for all non-API routes."""
        # Check if requesting a static file
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        # Otherwise, serve index.html for client-side routing
        return FileResponse(str(frontend_dist / "index.html"))
else:
    # Fallback when frontend is not built
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": f"Welcome to {settings.APP_NAME} API",
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "note": "Frontend not built. Run 'npm run build' in frontend directory."
        }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
