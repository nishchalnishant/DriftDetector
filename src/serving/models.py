"""
Pydantic models for request/response validation
"""

from typing import Optional
from pydantic import BaseModel, Field, validator


class SensorDataInput(BaseModel):
    """Input schema for sensor data prediction"""
    
    machine_id: str = Field(..., description="Unique machine identifier")
    vibration: float = Field(..., ge=0.0, le=100.0, description="Vibration level (0-100)")
    temperature: float = Field(..., ge=-50.0, le=200.0, description="Temperature in Celsius")
    rotational_speed: float = Field(..., ge=0.0, le=10000.0, description="Rotational speed in RPM")
    pressure: Optional[float] = Field(None, ge=0.0, description="Pressure reading")
    power_consumption: Optional[float] = Field(None, ge=0.0, description="Power consumption in kW")
    
    class Config:
        json_schema_extra = {
            "example": {
                "machine_id": "machine_001",
                "vibration": 45.2,
                "temperature": 75.5,
                "rotational_speed": 1500.0,
                "pressure": 2.5,
                "power_consumption": 15.3
            }
        }


class PredictionOutput(BaseModel):
    """Output schema for prediction response"""
    
    machine_id: str
    is_anomaly: bool = Field(..., description="Whether an anomaly is detected")
    anomaly_score: float = Field(..., description="Anomaly score (lower = more anomalous)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence (0-1)")
    timestamp: str = Field(..., description="Prediction timestamp")
    model_version: str = Field(..., description="Model version used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "machine_id": "machine_001",
                "is_anomaly": False,
                "anomaly_score": 0.45,
                "confidence": 0.89,
                "timestamp": "2024-01-26T12:00:00Z",
                "model_version": "v1.0.0"
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    
    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    model_version: Optional[str] = Field(None, description="Loaded model version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")


class ModelMetadata(BaseModel):
    """Model metadata response"""
    
    model_name: str
    model_version: str
    framework: str
    created_at: str
    features: list[str]
    contamination: float


class DriftMetrics(BaseModel):
    """Drift detection metrics"""
    
    drift_detected: bool = Field(..., description="Whether drift is detected")
    drift_score: float = Field(..., ge=0.0, description="Overall drift score")
    feature_drifts: dict[str, float] = Field(..., description="Per-feature drift scores")
    p_values: dict[str, float] = Field(..., description="Statistical test p-values")
    reference_window_size: int = Field(..., description="Size of reference data window")
    current_window_size: int = Field(..., description="Size of current data window")
    timestamp: str = Field(..., description="Drift calculation timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "drift_detected": True,
                "drift_score": 0.35,
                "feature_drifts": {
                    "vibration_mean_1h": 0.42,
                    "temperature_mean_1h": 0.18
                },
                "p_values": {
                    "vibration_mean_1h": 0.001,
                    "temperature_mean_1h": 0.25
                },
                "reference_window_size": 1000,
                "current_window_size": 100,
                "timestamp": "2024-01-26T12:00:00Z"
            }
        }


class BatchPredictionRequest(BaseModel):
    """Batch prediction request"""
    
    data: list[SensorDataInput] = Field(..., min_length=1, max_length=1000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {
                        "machine_id": "machine_001",
                        "vibration": 45.2,
                        "temperature": 75.5,
                        "rotational_speed": 1500.0
                    }
                ]
            }
        }


class BatchPredictionResponse(BaseModel):
    """Batch prediction response"""
    
    predictions: list[PredictionOutput]
    total_predicted: int
    anomalies_detected: int
    processing_time_ms: float
