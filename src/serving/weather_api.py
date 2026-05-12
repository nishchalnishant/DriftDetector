"""
Simple Weather Forecast API Server
Provides weather prediction endpoints for the DriftDetector UI
"""

import time
from datetime import datetime
from typing import Dict
import random

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from weather_models import WeatherDataInput, WeatherPredictionOutput

# ===========================
# Application Setup
# ===========================

app = FastAPI(
    title="Weather Forecast API",
    description="Weather forecasting with auto-retraining detection",
    version="1.0.0",
)

# CORS middleware - allow GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://nishchalnishant.github.io",
        "http://localhost:8080",
        "*"  # For development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
service_start_time = time.time()
prediction_count = 0
retraining_count = 0

# ===========================
# API Endpoints
# ===========================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Weather Forecast API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "stats": "/stats"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    uptime = time.time() - service_start_time
    
    return {
        "status": "healthy",
        "model_loaded": True,
        "model_version": "v1.0.0",
        "uptime_seconds": uptime,
        "uptime_formatted": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m"
    }


@app.post("/predict", response_model=WeatherPredictionOutput)
async def predict_weather(data: WeatherDataInput) -> WeatherPredictionOutput:
    """
    Predict weather forecast accuracy
    
    This simulates a weather forecasting model that:
    1. Takes current weather data as input
    2. Predicts future conditions
    3. Calculates forecast accuracy
    4. Determines if retraining is needed
    """
    global prediction_count, retraining_count
    
    try:
        # Increment counter
        prediction_count += 1
        
        # Simulate forecast accuracy calculation
        # In reality, this would compare predictions with actual weather
        accuracy = calculate_forecast_accuracy(data)
        
        # Determine if retraining needed (accuracy < 0.7)
        needs_retraining = accuracy < 0.7
        if needs_retraining:
            retraining_count += 1
        
        # Calculate confidence based on data patterns
        confidence = calculate_confidence(data)
        
        response = WeatherPredictionOutput(
            location=data.location,
            forecast_accuracy=accuracy,
            needs_retraining=needs_retraining,
            confidence=confidence,
            timestamp=datetime.utcnow().isoformat() + "Z",
            model_version="v1.0.0",
            input_data={
                "temperature": data.temperature,
                "pressure": data.pressure,
                "humidity": data.humidity,
                "wind_speed": data.wind_speed
            }
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Get service statistics"""
    uptime = time.time() - service_start_time
    
    accuracy = 0.95 if retraining_count == 0 else max(0.65, 0.95 - (retraining_count * 0.05))
    
    return {
        "uptime_seconds": uptime,
        "total_predictions": prediction_count,
        "retraining_triggers": retraining_count,
        "current_accuracy": round(accuracy, 2),
        "model_version": "v1.0.0"
    }


# ===========================
# Helper Functions
# ===========================

def calculate_forecast_accuracy(data: WeatherDataInput) -> float:
    """
    Calculate forecast accuracy based on weather data
    In production, this would compare predictions with actual weather
    
    For demo: simulate accuracy based on data characteristics
    Same input always gives same output (deterministic)
    """
    # Base accuracy
    accuracy = 0.85
    
    # Check for extreme conditions (reduces accuracy)
    if data.temperature < -10 or data.temperature > 40:
        accuracy -= 0.15  # Extreme temps are harder to predict
        
    if data.wind_speed > 20:
        accuracy -= 0.10  # Strong winds indicate unstable conditions
        
    if data.pressure < 980 or data.pressure > 1030:
        accuracy -= 0.10  # Unusual pressure patterns
    
    # Add small variation based on humidity (deterministic)
    # This makes different inputs have different accuracies
    humidity_factor = (data.humidity - 50) / 1000  # Small factor based on humidity
    accuracy += humidity_factor
    
    # Ensure accuracy is between 0 and 1
    return max(0.0, min(1.0, accuracy))


def calculate_confidence(data: WeatherDataInput) -> float:
    """
    Calculate prediction confidence based on data quality
    """
    confidence = 0.9
    
    # Standard conditions = high confidence
    if 15 <= data.temperature <= 30:
        confidence += 0.05
        
    if 1000 <= data.pressure <= 1020:
        confidence += 0.03
        
    if 40 <= data.humidity <= 70:
        confidence += 0.02
        
    return min(1.0, confidence)


# ===========================
# Main
# ===========================

if __name__ == "__main__":
    print("🌤️  Starting Weather Forecast API Server...")
    print("📍 Server will be available at:")
    print("   - http://localhost:8000")
    print("   - http://127.0.0.1:8000")
    print("\n🔗 API Documentation:")
    print("   - http://localhost:8000/docs")
    print("\n⏹️  Press CTRL+C to stop\n")
    
    uvicorn.run(
        "weather_api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
