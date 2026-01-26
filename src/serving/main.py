"""
FastAPI Inference Service for Predictive Maintenance

This service:
1. Loads model from Azure ML Model Registry
2. Fetches real-time features from Feast
3. Serves predictions via REST API
4. Logs requests/responses for drift detection
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import onnxruntime as rt
import uvicorn
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from feast import FeatureStore
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import pandas as pd

from models import (
    SensorDataInput,
    PredictionOutput,
    HealthResponse,
    ModelMetadata,
    BatchPredictionRequest,
    BatchPredictionResponse,
)

# ===========================
# Configuration
# ===========================

MODEL_NAME = os.getenv("MODEL_NAME", "anomaly-detection-model")
MODEL_VERSION = os.getenv("MODEL_VERSION", "latest")
FEAST_REPO_PATH = os.getenv("FEAST_REPO_PATH", "/app/features")
ANOMALY_THRESHOLD = float(os.getenv("ANOMALY_THRESHOLD", "-0.5"))
LOG_DIR = Path(os.getenv("LOG_DIR", "/app/logs"))

# ===========================
# Prometheus Metrics
# ===========================

REQUEST_COUNT = Counter(
    "inference_requests_total",
    "Total number of inference requests",
    ["endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "inference_request_duration_seconds",
    "Inference request latency in seconds",
    ["endpoint"]
)

ANOMALY_COUNT = Counter(
    "anomalies_detected_total",
    "Total number of anomalies detected"
)

# ===========================
# Application
# ===========================

app = FastAPI(
    title="Predictive Maintenance Inference API",
    description="Real-time anomaly detection for industrial equipment",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
model_session: Optional[rt.InferenceSession] = None
feature_store: Optional[FeatureStore] = None
model_metadata: dict = {}
service_start_time = time.time()


# ===========================
# Startup & Lifecycle
# ===========================

@app.on_event("startup")
async def startup_event():
    """Load model and initialize feature store on startup"""
    
    global model_session, feature_store, model_metadata
    
    print("Starting up inference service...")
    
    # Create log directory
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load model from Azure ML Registry
    print(f"Loading model {MODEL_NAME}:{MODEL_VERSION}...")
    try:
        credential = DefaultAzureCredential()
        ml_client = MLClient.from_config(credential=credential)
        
        # Download model
        model = ml_client.models.get(name=MODEL_NAME, version=MODEL_VERSION)
        model_path = Path(model.path) / "model.onnx"
        
        # Load ONNX model
        model_session = rt.InferenceSession(str(model_path))
        
        model_metadata = {
            "model_name": MODEL_NAME,
            "model_version": MODEL_VERSION,
            "framework": "onnx",
            "created_at": model.creation_context.created_at.isoformat() if model.creation_context else None,
        }
        
        print(f"Model loaded successfully: {model_metadata}")
        
    except Exception as e:
        print(f"Warning: Could not load model from Azure ML: {e}")
        print("Attempting to load local model...")
        
        # Fallback to local model for development
        local_model_path = Path("/app/models/model.onnx")
        if local_model_path.exists():
            model_session = rt.InferenceSession(str(local_model_path))
            model_metadata = {
                "model_name": "local-model",
                "model_version": "dev",
                "framework": "onnx",
            }
            print("Local model loaded successfully")
        else:
            print("ERROR: No model available!")
    
    # Initialize Feast feature store
    print("Initializing Feast feature store...")
    try:
        feature_store = FeatureStore(repo_path=FEAST_REPO_PATH)
        print("Feature store initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize feature store: {e}")
        feature_store = None
    
    print("Startup complete!")


# ===========================
# API Endpoints
# ===========================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    
    uptime = time.time() - service_start_time
    
    return HealthResponse(
        status="healthy" if model_session is not None else "degraded",
        model_loaded=model_session is not None,
        model_version=model_metadata.get("model_version"),
        uptime_seconds=uptime
    )


@app.get("/model/metadata", response_model=ModelMetadata)
async def get_model_metadata():
    """Get model metadata"""
    
    if not model_session:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return ModelMetadata(
        model_name=model_metadata.get("model_name", "unknown"),
        model_version=model_metadata.get("model_version", "unknown"),
        framework=model_metadata.get("framework", "onnx"),
        created_at=model_metadata.get("created_at", datetime.utcnow().isoformat()),
        features=[],  # TODO: Extract from model
        contamination=0.1  # TODO: Extract from model metadata
    )


@app.post("/predict", response_model=PredictionOutput)
async def predict(
    data: SensorDataInput,
    background_tasks: BackgroundTasks
) -> PredictionOutput:
    """
    Predict anomaly for a single sensor reading
    
    This endpoint:
    1. Fetches features from Feast online store
    2. Runs inference using ONNX model
    3. Returns prediction with anomaly score
    4. Logs request for drift detection
    """
    
    start_time = time.time()
    
    try:
        if not model_session:
            REQUEST_COUNT.labels(endpoint="predict", status="error").inc()
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        # Fetch features from Feast
        features = await fetch_features(data.machine_id)
        
        # Prepare input
        input_data = prepare_input(data, features)
        
        # Run inference
        input_name = model_session.get_inputs()[0].name
        output_names = [output.name for output in model_session.get_outputs()]
        
        predictions = model_session.run(output_names, {input_name: input_data})
        
        # Parse prediction
        anomaly_score = float(predictions[0][0])
        is_anomaly = anomaly_score < ANOMALY_THRESHOLD
        
        # Calculate confidence (based on distance from threshold)
        confidence = abs(anomaly_score - ANOMALY_THRESHOLD) / (1.0 + abs(ANOMALY_THRESHOLD))
        confidence = min(max(confidence, 0.0), 1.0)
        
        # Create response
        response = PredictionOutput(
            machine_id=data.machine_id,
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            confidence=confidence,
            timestamp=datetime.utcnow().isoformat(),
            model_version=model_metadata.get("model_version", "unknown")
        )
        
        # Update metrics
        REQUEST_COUNT.labels(endpoint="predict", status="success").inc()
        REQUEST_LATENCY.labels(endpoint="predict").observe(time.time() - start_time)
        
        if is_anomaly:
            ANOMALY_COUNT.inc()
        
        # Log request for drift detection
        background_tasks.add_task(log_request, data, response)
        
        return response
        
    except Exception as e:
        REQUEST_COUNT.labels(endpoint="predict", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch(request: BatchPredictionRequest) -> BatchPredictionResponse:
    """Batch prediction endpoint"""
    
    start_time = time.time()
    
    predictions = []
    anomaly_count = 0
    
    for sensor_data in request.data:
        try:
            pred = await predict(sensor_data, BackgroundTasks())
            predictions.append(pred)
            if pred.is_anomaly:
                anomaly_count += 1
        except Exception as e:
            print(f"Error predicting for machine {sensor_data.machine_id}: {e}")
    
    processing_time = (time.time() - start_time) * 1000  # Convert to ms
    
    return BatchPredictionResponse(
        predictions=predictions,
        total_predicted=len(predictions),
        anomalies_detected=anomaly_count,
        processing_time_ms=processing_time
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ===========================
# Helper Functions
# ===========================

async def fetch_features(machine_id: str) -> dict:
    """Fetch features from Feast online store"""
    
    if not feature_store:
        return {}
    
    try:
        features = feature_store.get_online_features(
            features=[
                "sensor_stats_1h:vibration_mean_1h",
                "sensor_stats_1h:temperature_mean_1h",
                "sensor_stats_1h:rotational_speed_mean_1h",
            ],
            entity_rows=[{"machine_id": machine_id}],
        ).to_dict()
        
        return features
        
    except Exception as e:
        print(f"Error fetching features: {e}")
        return {}


def prepare_input(data: SensorDataInput, features: dict) -> np.ndarray:
    """Prepare input array for model"""
    
    # Combine sensor data with features
    input_features = [
        data.vibration,
        data.temperature,
        data.rotational_speed,
        features.get("vibration_mean_1h", [0.0])[0],
        features.get("temperature_mean_1h", [0.0])[0],
        features.get("rotational_speed_mean_1h", [0.0])[0],
    ]
    
    return np.array([input_features], dtype=np.float32)


async def log_request(data: SensorDataInput, response: PredictionOutput):
    """Log request/response for drift detection"""
    
    log_file = LOG_DIR / f"predictions_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
    
    log_entry = {
        "timestamp": response.timestamp,
        "machine_id": data.machine_id,
        "input": data.dict(),
        "output": response.dict(),
    }
    
    import json
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


# ===========================
# Main
# ===========================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
