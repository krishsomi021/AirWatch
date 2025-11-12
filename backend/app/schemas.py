"""Pydantic models for API requests and responses."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class PredictionRequest(BaseModel):
    """Request model for air quality prediction."""
    zip_code: Optional[str] = Field(None, description="New Jersey ZIP code")
    location: Optional[str] = Field(None, description="Location name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "zip_code": "08901",
                "location": "New Brunswick"
            }
        }


class PredictionResponse(BaseModel):
    """Response model for air quality prediction."""
    date: str = Field(..., description="Target date for prediction")
    location: str = Field(..., description="Location (ZIP or region)")
    prob_unhealthy: float = Field(..., description="Probability of unhealthy AQI (0-1)")
    classification: str = Field(..., description="Safe or Unhealthy")
    threshold: float = Field(..., description="Classification threshold used")
    confidence: str = Field(..., description="Low, Medium, or High confidence")
    aqi_category: str = Field(..., description="AQI category description")
    top_factors: List[str] = Field(..., description="Top contributing factors")
    
    class Config:
        json_schema_extra = {
            "example": {
                "date": "2025-11-12",
                "location": "08901",
                "prob_unhealthy": 0.37,
                "classification": "Safe",
                "threshold": 0.40,
                "confidence": "High",
                "aqi_category": "Good to Moderate",
                "top_factors": [
                    "Low previous day AQI",
                    "Good wind conditions",
                    "Recent precipitation"
                ]
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="API status")
    model_loaded: bool = Field(..., description="Whether ML model is loaded")
    version: str = Field(..., description="API version")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "model_loaded": True,
                "version": "1.0.0"
            }
        }


class FeatureInput(BaseModel):
    """Direct feature input for prediction (advanced use)."""
    aqi_prev1: float = Field(..., description="AQI from previous day")
    aqi_prev2: Optional[float] = Field(None, description="AQI from 2 days ago")
    aqi_3day_avg: Optional[float] = Field(None, description="3-day rolling average AQI")
    temp_max: float = Field(..., description="Forecasted max temperature (F)")
    wind_avg: float = Field(..., description="Forecasted average wind speed (mph)")
    rh_avg: Optional[float] = Field(None, description="Relative humidity (%)")
    precip: Optional[float] = Field(0.0, description="Precipitation amount (inches)")
    month: int = Field(..., description="Month (1-12)")
    day_of_week: int = Field(..., description="Day of week (0=Monday, 6=Sunday)")
    is_weekend: bool = Field(..., description="Is it a weekend?")
    
    class Config:
        json_schema_extra = {
            "example": {
                "aqi_prev1": 45.0,
                "aqi_prev2": 38.0,
                "aqi_3day_avg": 42.0,
                "temp_max": 75.0,
                "wind_avg": 8.5,
                "rh_avg": 65.0,
                "precip": 0.0,
                "month": 7,
                "day_of_week": 2,
                "is_weekend": False
            }
        }
