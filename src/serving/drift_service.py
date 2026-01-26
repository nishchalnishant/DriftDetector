"""
Evidently AI Drift Detection Service

This sidecar service:
1. Collects inference logs from the main application
2. Calculates data drift metrics using Evidently AI
3. Exposes metrics for Prometheus
4. Triggers alerts when drift exceeds threshold
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd
import uvicorn
from evidently import ColumnMapping
from evidently.metric_preset import DataDriftPreset
from evidently.report import Report
from evidently.metrics import DataDriftTable, DatasetDriftMetric
from fastapi import FastAPI, HTTPException, BackgroundTasks
from prometheus_client import Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from pydantic import BaseModel

# ===========================
# Configuration
# ===========================

LOG_DIR = Path(os.getenv("LOG_DIR", "/app/logs"))
REFERENCE_DATA_PATH = os.getenv("REFERENCE_DATA_PATH", "/app/data/reference.parquet")
DRIFT_THRESHOLD = float(os.getenv("DRIFT_THRESHOLD", "0.3"))
DRIFT_WINDOW_SIZE = int(os.getenv("DRIFT_WINDOW_SIZE", "1000"))
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "300"))

# ===========================
# Prometheus Metrics
# ===========================

DRIFT_SCORE_GAUGE = Gauge(
    "data_drift_score",
    "Overall data drift score",
    ["feature"]
)

DRIFT_DETECTED_COUNTER = Counter(
    "drift_detections_total",
    "Total number of drift detections"
)

FEATURES_DRIFTED_GAUGE = Gauge(
    "features_with_drift",
    "Number of features experiencing drift"
)

# ===========================
# Application
# ===========================

app = FastAPI(
    title="Drift Detection Service",
    description="Real-time data drift monitoring using Evidently AI",
    version="1.0.0",
)

# Global state
reference_data: Optional[pd.DataFrame] = None
last_drift_check: Optional[datetime] = None
current_drift_report: Optional[dict] = None


# ===========================
# Data Models
# ===========================

class DriftCalculationRequest(BaseModel):
    """Request to calculate drift on provided data"""
    
    current_data: List[Dict]
    use_cached_reference: bool = True


class DriftResponse(BaseModel):
    """Drift detection response"""
    
    drift_detected: bool
    drift_score: float
    feature_drifts: Dict[str, float]
    p_values: Dict[str, float]
    reference_window_size: int
    current_window_size: int
    timestamp: str
    drift_threshold: float


# ===========================
# Startup & Lifecycle
# ===========================

@app.on_event("startup")
async def startup_event():
    """Load reference data on startup"""
    
    global reference_data
    
    print("Starting drift detection service...")
    
    # Load reference data
    ref_path = Path(REFERENCE_DATA_PATH)
    if ref_path.exists():
        print(f"Loading reference data from {ref_path}...")
        reference_data = pd.read_parquet(ref_path)
        print(f"Loaded {len(reference_data)} reference samples")
    else:
        print(f"Warning: Reference data not found at {ref_path}")
        print("Drift detection will use the first batch as reference")
        reference_data = None
    
    # Start background drift monitoring
    import asyncio
    asyncio.create_task(periodic_drift_check())
    
    print("Drift detection service ready!")


# ===========================
# API Endpoints
# ===========================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    
    return {
        "status": "healthy",
        "reference_data_loaded": reference_data is not None,
        "last_check": last_drift_check.isoformat() if last_drift_check else None,
        "drift_threshold": DRIFT_THRESHOLD
    }


@app.post("/calculate_drift", response_model=DriftResponse)
async def calculate_drift(request: DriftCalculationRequest) -> DriftResponse:
    """
    Calculate drift metrics for provided data
    
    Compares current data against reference distribution using:
    - Wasserstein distance for continuous features
    - Chi-squared test for categorical features
    """
    
    global reference_data, current_drift_report
    
    try:
        # Convert current data to DataFrame
        current_df = pd.DataFrame(request.current_data)
        
        if current_df.empty:
            raise HTTPException(status_code=400, detail="Current data is empty")
        
        # Use cached reference or provided reference
        ref_df = reference_data
        
        if ref_df is None:
            # If no reference data, use the current batch as reference for future
            print("No reference data available, using current batch as baseline")
            reference_data = current_df.copy()
            return DriftResponse(
                drift_detected=False,
                drift_score=0.0,
                feature_drifts={},
                p_values={},
                reference_window_size=len(current_df),
                current_window_size=len(current_df),
                timestamp=datetime.utcnow().isoformat(),
                drift_threshold=DRIFT_THRESHOLD
            )
        
        # Ensure both dataframes have the same columns
        common_cols = list(set(ref_df.columns) & set(current_df.columns))
        feature_cols = [col for col in common_cols if col not in ['machine_id', 'timestamp', 'event_timestamp']]
        
        if not feature_cols:
            raise HTTPException(status_code=400, detail="No common features found")
        
        ref_df = ref_df[feature_cols]
        current_df = current_df[feature_cols]
        
        # Create Evidently report
        print("Running Evidently drift detection...")
        report = Report(metrics=[
            DataDriftPreset(),
            DatasetDriftMetric(),
        ])
        
        report.run(
            reference_data=ref_df,
            current_data=current_df,
            column_mapping=ColumnMapping()
        )
        
        # Extract results
        report_dict = report.as_dict()
        
        # Parse drift metrics
        drift_results = parse_drift_report(report_dict, feature_cols)
        
        # Update Prometheus metrics
        for feature, score in drift_results["feature_drifts"].items():
            DRIFT_SCORE_GAUGE.labels(feature=feature).set(score)
        
        FEATURES_DRIFTED_GAUGE.set(
            sum(1 for score in drift_results["feature_drifts"].values() if score > DRIFT_THRESHOLD)
        )
        
        if drift_results["drift_detected"]:
            DRIFT_DETECTED_COUNTER.inc()
        
        # Cache results
        current_drift_report = drift_results
        
        # Create response
        response = DriftResponse(
            drift_detected=drift_results["drift_detected"],
            drift_score=drift_results["drift_score"],
            feature_drifts=drift_results["feature_drifts"],
            p_values=drift_results["p_values"],
            reference_window_size=len(ref_df),
            current_window_size=len(current_df),
            timestamp=datetime.utcnow().isoformat(),
            drift_threshold=DRIFT_THRESHOLD
        )
        
        # If drift detected, trigger alert
        if response.drift_detected:
            await trigger_drift_alert(response)
        
        return response
        
    except Exception as e:
        print(f"Error calculating drift: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/drift/latest")
async def get_latest_drift():
    """Get the latest drift report"""
    
    if current_drift_report is None:
        return {"message": "No drift report available yet"}
    
    return current_drift_report


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ===========================
# Helper Functions
# ===========================

def parse_drift_report(report_dict: dict, feature_cols: List[str]) -> dict:
    """Parse Evidently drift report into structured format"""
    
    try:
        metrics = report_dict.get("metrics", [])
        
        # Find DatasetDriftMetric
        dataset_drift = None
        for metric in metrics:
            if metric.get("metric") == "DatasetDriftMetric":
                dataset_drift = metric.get("result", {})
                break
        
        if not dataset_drift:
            print("Warning: Could not find drift metrics in report")
            return {
                "drift_detected": False,
                "drift_score": 0.0,
                "feature_drifts": {},
                "p_values": {}
            }
        
        # Extract drift metrics
        drift_by_columns = dataset_drift.get("drift_by_columns", {})
        
        feature_drifts = {}
        p_values = {}
        
        for col in feature_cols:
            col_drift = drift_by_columns.get(col, {})
            feature_drifts[col] = col_drift.get("drift_score", 0.0)
            p_values[col] = col_drift.get("drift_detected", False)
        
        # Calculate overall drift score (max drift across features)
        overall_drift_score = max(feature_drifts.values()) if feature_drifts else 0.0
        
        # Determine if drift is detected
        drift_detected = overall_drift_score > DRIFT_THRESHOLD
        
        return {
            "drift_detected": drift_detected,
            "drift_score": overall_drift_score,
            "feature_drifts": feature_drifts,
            "p_values": p_values
        }
        
    except Exception as e:
        print(f"Error parsing drift report: {e}")
        return {
            "drift_detected": False,
            "drift_score": 0.0,
            "feature_drifts": {},
            "p_values": {}
        }


async def load_recent_predictions() -> pd.DataFrame:
    """Load recent predictions from log files"""
    
    try:
        # Get today's log file
        today = datetime.utcnow().strftime("%Y%m%d")
        log_file = LOG_DIR / f"predictions_{today}.jsonl"
        
        if not log_file.exists():
            print(f"No log file found: {log_file}")
            return pd.DataFrame()
        
        # Read JSONL file
        predictions = []
        with open(log_file, "r") as f:
            for line in f:
                try:
                    pred = json.loads(line)
                    predictions.append(pred["input"])
                except json.JSONDecodeError:
                    continue
        
        if not predictions:
            return pd.DataFrame()
        
        df = pd.DataFrame(predictions)
        
        # Limit to window size
        if len(df) > DRIFT_WINDOW_SIZE:
            df = df.tail(DRIFT_WINDOW_SIZE)
        
        return df
        
    except Exception as e:
        print(f"Error loading predictions: {e}")
        return pd.DataFrame()


async def periodic_drift_check():
    """Background task to periodically check for drift"""
    
    global last_drift_check
    
    while True:
        try:
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)
            
            print("Running periodic drift check...")
            
            # Load recent predictions
            current_data = await load_recent_predictions()
            
            if current_data.empty:
                print("No data available for drift check")
                continue
            
            # Calculate drift
            request = DriftCalculationRequest(
                current_data=current_data.to_dict('records'),
                use_cached_reference=True
            )
            
            result = await calculate_drift(request)
            last_drift_check = datetime.utcnow()
            
            print(f"Drift check complete: drift_detected={result.drift_detected}, score={result.drift_score}")
            
        except Exception as e:
            print(f"Error in periodic drift check: {e}")


async def trigger_drift_alert(drift_response: DriftResponse):
    """Trigger alert when drift is detected"""
    
    print(f"⚠️  DRIFT ALERT: Overall score {drift_response.drift_score:.3f} exceeds threshold {DRIFT_THRESHOLD}")
    print(f"Features with drift: {[f for f, s in drift_response.feature_drifts.items() if s > DRIFT_THRESHOLD]}")
    
    # TODO: Implement alerting mechanism
    # - Send to Azure Monitor
    # - Trigger webhook for model retraining
    # - Send notification via email/Slack
    
    # For now, write to alert file
    alert_file = LOG_DIR / "drift_alerts.jsonl"
    with open(alert_file, "a") as f:
        f.write(json.dumps({
            "timestamp": drift_response.timestamp,
            "drift_score": drift_response.drift_score,
            "feature_drifts": drift_response.feature_drifts,
            "threshold": drift_response.drift_threshold
        }) + "\n")


# ===========================
# Main
# ===========================

if __name__ == "__main__":
    import asyncio
    
    uvicorn.run(
        "drift_service:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )
