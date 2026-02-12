"""Main FastAPI application for AirWatch AQI Prediction API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import get_settings
from backend.app.routers import health, predict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="AirWatch AQI Prediction API",
    description="Next-day air quality classification for New Jersey",
    version="1.0.0",
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    openapi_url=f"{settings.api_prefix}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
app.include_router(predict.router, prefix=settings.api_prefix, tags=["prediction"])


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting AirWatch AQI Prediction API")
    logger.info(f"API documentation available at {settings.api_prefix}/docs")
    
    # Try to preload model
    try:
        from backend.app.model_loader import get_model_loader
        model_loader = get_model_loader(
            settings.model_path,
            settings.feature_list_path
        )
        logger.info("✓ Model loaded successfully")
    except Exception as e:
        logger.warning(f"⚠ Could not preload model: {e}")
        logger.warning("Model will be loaded on first prediction request")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down AirWatch API")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AirWatch AQI Prediction API",
        "version": "1.0.0",
        "description": "Next-day air quality classification for New Jersey",
        "docs": f"{settings.api_prefix}/docs",
        "health": f"{settings.api_prefix}/health",
        "predict": f"{settings.api_prefix}/predict"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
