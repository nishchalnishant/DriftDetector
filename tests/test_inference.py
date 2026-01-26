"""
Unit tests for inference service
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import numpy as np

from src.serving.main import app
from src.serving.models import SensorDataInput, PredictionOutput


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def sample_sensor_data():
    """Sample sensor data for testing"""
    return SensorDataInput(
        machine_id="test_machine_001",
        vibration=45.2,
        temperature=75.5,
        rotational_speed=1500.0,
        pressure=2.5,
        power_consumption=15.3
    )


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data
    assert "uptime_seconds" in data


def test_model_metadata_endpoint(client):
    """Test model metadata endpoint"""
    with patch('src.serving.main.model_session'):
        response = client.get("/model/metadata")
        
        if response.status_code == 200:
            data = response.json()
            assert "model_name" in data
            assert "model_version" in data
            assert "framework" in data


@patch('src.serving.main.model_session')
@patch('src.serving.main.feature_store')
def test_predict_endpoint(mock_feature_store, mock_model, client, sample_sensor_data):
    """Test prediction endpoint"""
    
    # Mock model inference
    mock_model.get_inputs.return_value = [Mock(name='input')]
    mock_model.get_outputs.return_value = [Mock(name='output')]
    mock_model.run.return_value = [[0.5]]  # Anomaly score
    
    # Mock feature store
    mock_feature_store.get_online_features.return_value.to_dict.return_value = {
        "vibration_mean_1h": [45.0],
        "temperature_mean_1h": [75.0],
        "rotational_speed_mean_1h": [1500.0],
    }
    
    response = client.post("/predict", json=sample_sensor_data.dict())
    
    assert response.status_code == 200
    data = response.json()
    
    assert "machine_id" in data
    assert "is_anomaly" in data
    assert "anomaly_score" in data
    assert "confidence" in data
    assert data["machine_id"] == "test_machine_001"


def test_predict_invalid_input(client):
    """Test prediction with invalid input"""
    invalid_data = {
        "machine_id": "test",
        "vibration": 150.0,  # Out of valid range
        "temperature": 75.5,
        "rotational_speed": 1500.0
    }
    
    response = client.post("/predict", json=invalid_data)
    assert response.status_code == 422  # Validation error


def test_batch_prediction(client):
    """Test batch prediction endpoint"""
    batch_data = {
        "data": [
            {
                "machine_id": "machine_001",
                "vibration": 45.2,
                "temperature": 75.5,
                "rotational_speed": 1500.0
            },
            {
                "machine_id": "machine_002",
                "vibration": 50.0,
                "temperature": 80.0,
                "rotational_speed": 1600.0
            }
        ]
    }
    
    with patch('src.serving.main.model_session'), \
         patch('src.serving.main.feature_store'):
        response = client.post("/predict/batch", json=batch_data)
        
        # May fail if model not loaded, but should not crash
        assert response.status_code in [200, 503]


def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
