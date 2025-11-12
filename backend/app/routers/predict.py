"""Prediction endpoint for air quality classification."""
from fastapi import APIRouter, Depends, HTTPException
from backend.app.schemas import PredictionRequest, PredictionResponse, FeatureInput
from backend.app.config import get_settings, Settings
from backend.app.model_loader import get_model_loader
from backend.app.data_collector import DataCollector, get_coordinates_for_zip
from backend.app.ml.features import FeatureEngineer
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Cache for daily predictions
prediction_cache = {}


@router.post("/predict", response_model=PredictionResponse)
@router.get("/predict", response_model=PredictionResponse)
async def predict_air_quality(
    request: PredictionRequest = None,
    zip_code: str = None,
    settings: Settings = Depends(get_settings)
):
    """
    Predict next-day air quality classification.
    
    Can be called with:
    - POST with PredictionRequest body
    - GET with zip_code query parameter
    - GET with no parameters (returns statewide prediction)
    """
    # Get zip code from request or query param
    if request and request.zip_code:
        zip_code = request.zip_code
    elif not zip_code:
        zip_code = "08901"  # Default: New Brunswick, NJ
    
    # Check cache first
    cache_key = f"{zip_code}_{datetime.now().date()}"
    if cache_key in prediction_cache:
        logger.info(f"Returning cached prediction for {zip_code}")
        return prediction_cache[cache_key]
    
    try:
        # Load model
        model_loader = get_model_loader(
            settings.model_path,
            settings.feature_list_path
        )
        
        # Collect current data
        data_collector = DataCollector(
            airnow_api_key=settings.airnow_api_key,
            nws_user_agent=settings.nws_user_agent
        )
        
        # Get current AQI (for lag features)
        current_aqi_data = data_collector.fetch_airnow_current(zip_code)
        
        if current_aqi_data and 'AQI' in current_aqi_data:
            current_aqi = current_aqi_data['AQI']
        else:
            logger.warning("Could not fetch current AQI, using default")
            current_aqi = 50.0
        
        # Get weather forecast for tomorrow
        lat, lon = get_coordinates_for_zip(zip_code)
        weather_forecast = data_collector.fetch_nws_forecast(lat, lon)
        
        # Build feature dictionary
        tomorrow = datetime.now() + timedelta(days=1)
        
        features = {
            'AQI_prev1': current_aqi,
            'AQI_prev2': current_aqi * 0.95,  # Estimate (would need historical data)
            'AQI_3day_avg': current_aqi,
            'AQI_7day_avg': current_aqi,
            'AQI_3day_max': current_aqi * 1.1,
            'AQI_7day_std': 5.0,
            'AQI_trend': 0.0,
            'temp_max': weather_forecast.get('temp', 70.0),
            'wind_avg': weather_forecast.get('wind_speed', 8.0),
            'precip': 0.1 if weather_forecast.get('precip_prob', 0) > 50 else 0.0,
            'rh_avg': 60.0,  # Would need from detailed forecast
            'month': tomorrow.month,
            'day_of_week': tomorrow.weekday(),
            'is_weekend': 1 if tomorrow.weekday() >= 5 else 0,
            'day_of_year': tomorrow.timetuple().tm_yday,
            'season': tomorrow.month % 12 // 3,
            'is_holiday': 0,
        }
        
        # Create derived features
        feature_engineer = FeatureEngineer()
        feature_df = feature_engineer.create_features_from_dict(features)
        feature_dict = feature_df.iloc[0].to_dict()
        
        # Get prediction
        result = model_loader.predict(feature_dict)
        prob_unhealthy = result['probability']
        
        # Classify based on threshold
        is_unhealthy = prob_unhealthy >= settings.prediction_threshold
        classification = "Unhealthy" if is_unhealthy else "Safe"
        
        # Determine confidence
        if abs(prob_unhealthy - settings.prediction_threshold) > 0.2:
            confidence = "High"
        elif abs(prob_unhealthy - settings.prediction_threshold) > 0.1:
            confidence = "Medium"
        else:
            confidence = "Low"
        
        # Get AQI category description
        if is_unhealthy:
            aqi_category = "Unhealthy for Sensitive Groups or worse (AQI ≥ 101)"
        else:
            aqi_category = "Good to Moderate (AQI ≤ 100)"
        
        # Get top factors
        top_factors = model_loader.get_top_factors(feature_dict, settings.prediction_threshold)
        
        # Create response
        response = PredictionResponse(
            date=tomorrow.strftime("%Y-%m-%d"),
            location=zip_code,
            prob_unhealthy=round(prob_unhealthy, 3),
            classification=classification,
            threshold=settings.prediction_threshold,
            confidence=confidence,
            aqi_category=aqi_category,
            top_factors=top_factors
        )
        
        # Cache the prediction
        prediction_cache[cache_key] = response
        
        return response
        
    except Exception as e:
        logger.error(f"Error making prediction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post("/predict/features", response_model=PredictionResponse)
async def predict_with_features(
    features: FeatureInput,
    settings: Settings = Depends(get_settings)
):
    """
    Advanced endpoint: predict with directly provided features.
    Useful for testing or when you have pre-computed features.
    """
    try:
        # Load model
        model_loader = get_model_loader(
            settings.model_path,
            settings.feature_list_path
        )
        
        # Convert Pydantic model to dict
        feature_dict = features.dict()
        
        # Create derived features
        feature_engineer = FeatureEngineer()
        feature_df = feature_engineer.create_features_from_dict(feature_dict)
        full_features = feature_df.iloc[0].to_dict()
        
        # Get prediction
        result = model_loader.predict(full_features)
        prob_unhealthy = result['probability']
        
        # Classify
        is_unhealthy = prob_unhealthy >= settings.prediction_threshold
        classification = "Unhealthy" if is_unhealthy else "Safe"
        
        # Confidence
        if abs(prob_unhealthy - settings.prediction_threshold) > 0.2:
            confidence = "High"
        elif abs(prob_unhealthy - settings.prediction_threshold) > 0.1:
            confidence = "Medium"
        else:
            confidence = "Low"
        
        # AQI category
        if is_unhealthy:
            aqi_category = "Unhealthy for Sensitive Groups or worse (AQI ≥ 101)"
        else:
            aqi_category = "Good to Moderate (AQI ≤ 100)"
        
        # Top factors
        top_factors = model_loader.get_top_factors(full_features, settings.prediction_threshold)
        
        tomorrow = datetime.now() + timedelta(days=1)
        
        return PredictionResponse(
            date=tomorrow.strftime("%Y-%m-%d"),
            location="Custom",
            prob_unhealthy=round(prob_unhealthy, 3),
            classification=classification,
            threshold=settings.prediction_threshold,
            confidence=confidence,
            aqi_category=aqi_category,
            top_factors=top_factors
        )
        
    except Exception as e:
        logger.error(f"Error making prediction with features: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")
