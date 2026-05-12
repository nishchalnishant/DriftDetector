"""
Pydantic models for weather data prediction
"""

from typing import Optional
from pydantic import BaseModel, Field


class WeatherDataInput(BaseModel):
    """Input schema for weather data prediction"""
    
    location: str = Field(..., description="Location name (e.g., New York, London)")
    temperature: float = Field(..., ge=-50.0, le=60.0, description="Temperature in Celsius")
    pressure: float = Field(..., ge=800.0, le=1100.0, description="Atmospheric pressure in hPa")
    humidity: float = Field(..., ge=0.0, le=100.0, description="Humidity percentage")
    wind_speed: float = Field(..., ge=0.0, le=50.0, description="Wind speed in m/s")
    
    class Config:
        json_schema_extra = {
            "example": {
                "location": "New York",
                "temperature": 22.5,
                "pressure": 1013.0,
                "humidity": 65.0,
                "wind_speed": 5.2
            }
        }


class WeatherPredictionOutput(BaseModel):
    """Output schema for weather prediction response"""
    
    location: str
    forecast_accuracy: float = Field(..., ge=0.0, le=1.0, description="Forecast accuracy score (0-1)")
    needs_retraining: bool = Field(..., description="Whether model needs retraining")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence (0-1)")
    timestamp: str = Field(..., description="Prediction timestamp")
    model_version: str = Field(..., description="Model version used")
    input_data: dict = Field(..., description="Input weather parameters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "location": "New York",
                "forecast_accuracy": 0.92,
                "needs_retraining": False,
                "confidence": 0.89,
                "timestamp": "2026-01-28T12:00:00Z",
                "model_version": "v1.0.0",
                "input_data": {
                    "temperature": 22.5,
                    "pressure": 1013.0,
                    "humidity": 65.0,
                    "wind_speed": 5.2
                }
            }
        }
