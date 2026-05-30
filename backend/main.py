"""
SmartRescue AI — Backend Entrypoint
Production FastAPI application for the AI-powered road accident response ecosystem.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config.settings import get_settings
from app.firebase.client import initialize_firebase
from app.ml.predictor import predictor
from app.utils.rate_limiter import setup_rate_limiting
from app.utils.logger import get_logger

# Import routers
from app.routes.auth import router as auth_router
from app.routes.traveller import router as traveller_router
from app.routes.ambulance import router as ambulance_router
from app.routes.hospital import router as hospital_router
from app.routes.admin import router as admin_router
from app.websocket.handlers import router as ws_router

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown lifecycle events."""
    logger.info("Initializing SmartRescue AI Backend...")
    
    # 1. Initialize Firebase Admin SDK
    try:
        initialize_firebase()
        logger.info("Firebase Admin SDK successfully initialized.")
    except Exception as e:
        logger.error(f"CRITICAL: Failed to initialize Firebase: {e}")
        
    # 2. Load ML RandomForest Model
    try:
        model_loaded = predictor.load_model()
        if model_loaded:
            logger.info("RandomForest accident detection model successfully loaded.")
        else:
            logger.warning("Mock predictor is active: Model pkl file missing.")
    except Exception as e:
        logger.error(f"CRITICAL: Failed to load RandomForest ML model: {e}")

    yield
    
    logger.info("Shutting down SmartRescue AI Backend...")


# Instantiate FastAPI
settings = get_settings()
app = FastAPI(
    title="SmartRescue AI Backend",
    description="""
    Production-grade AI-powered road accident emergency response backend.
    
    Supports:
    * AI Accident Detection (RandomForest prediction & buffer filters)
    * Real-time GPS Location tracking (WebSockets)
    * Role-Based Access Control (Firebase + custom JWT verification)
    * Immediate Ambulance Allocation & Reassignment workflows
    * Pre-arrival Hospital trauma care preparations
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup SlowAPI Rate Limiting
setup_rate_limiting(app)

# Include HTTP API routers
app.include_router(auth_router)
app.include_router(traveller_router)
app.include_router(ambulance_router)
app.include_router(hospital_router)
app.include_router(admin_router)

# Include WebSocket routes
app.include_router(ws_router)


@app.get("/", tags=["Health Check"])
async def root():
    """Health check endpoint to verify backend status."""
    ml_info = predictor.get_model_info()
    return {
        "status": "healthy",
        "app_name": "SmartRescue AI Backend",
        "version": "1.0.0",
        "ml_model_loaded": ml_info["model_loaded"],
        "ml_model_info": ml_info
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
