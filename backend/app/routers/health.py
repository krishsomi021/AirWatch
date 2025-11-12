"""Health check endpoint."""
from fastapi import APIRouter, Depends
from backend.app.schemas import HealthResponse
from backend.app.config import get_settings, Settings
from backend.app.model_loader import get_model_loader

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)):
    """
    Health check endpoint to verify API is running and model is loaded.
    """
    try:
        model_loader = get_model_loader(
            settings.model_path,
            settings.feature_list_path
        )
        model_loaded = model_loader.is_loaded()
    except Exception:
        model_loaded = False
    
    return HealthResponse(
        status="ok",
        model_loaded=model_loaded,
        version="1.0.0"
    )
