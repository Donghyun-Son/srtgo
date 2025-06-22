from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import create_db_and_tables
from app.core.error_handler import srtgo_exception_handler, SRTGoException
from app.api import api_router
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# Add exception handlers
app.add_exception_handler(SRTGoException, srtgo_exception_handler)
app.add_exception_handler(Exception, srtgo_exception_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Include WebSocket routes directly at app level for CORS
from app.api.routes.websocket import router as ws_router
app.include_router(ws_router, prefix="/api/v1/ws")


@app.on_event("startup")
def on_startup():
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"CORS allowed origins: {settings.BACKEND_CORS_ORIGINS}")
    create_db_and_tables()
    logger.info("Database tables created successfully")


@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.APP_NAME}"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}