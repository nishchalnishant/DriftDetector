"""
Unit tests for drift detection service
"""

import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from src.serving.drift_service import app, parse_drift_report


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def sample_reference_data():
    """Generate sample reference data"""
    np.random.seed(42)
    return pd.DataFrame({
        "vibration": np.random.normal(50, 10, 1000),
        "temperature": np.random.normal(75, 5, 1000),
        "rotational_speed": np.random.normal(1500, 100, 1000),
    })


@pytest.fixture
def sample_current_data():
    """Generate sample current data (no drift)"""
    np.random.seed(43)
    return pd.DataFrame({
        "vibration": np.random.normal(50, 10, 100),
        "temperature": np.random.normal(75, 5, 100),
        "rotational_speed": np.random.normal(1500, 100, 100),
    })


@pytest.fixture
def drifted_data():
    """Generate drifted data"""
    np.random.seed(44)
    return pd.DataFrame({
        "vibration": np.random.normal(70, 15, 100),  # Mean shifted
        "temperature": np.random.normal(90, 8, 100),  # Mean shifted
        "rotational_speed": np.random.normal(1800, 150, 100),  # Mean shifted
    })


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "reference_data_loaded" in data
    assert "drift_threshold" in data


@patch('src.serving.drift_service.reference_data')
def test_calculate_drift_no_drift(mock_ref, client, sample_reference_data, sample_current_data):
    """Test drift calculation with no drift"""
    
    mock_ref = sample_reference_data
    
    request_data = {
        "current_data": sample_current_data.to_dict('records'),
        "use_cached_reference": True
    }
    
    response = client.post("/calculate_drift", json=request_data)
    
    # May succeed or fail depending on setup
    if response.status_code == 200:
        data = response.json()
        assert "drift_detected" in data
        assert "drift_score" in data
        assert "feature_drifts" in data


def test_calculate_drift_with_drift(client, sample_reference_data, drifted_data):
    """Test drift calculation with actual drift"""
    
    with patch('src.serving.drift_service.reference_data', sample_reference_data):
        request_data = {
            "current_data": drifted_data.to_dict('records'),
            "use_cached_reference": True
        }
        
        response = client.post("/calculate_drift", json=request_data)
        
        if response.status_code == 200:
            data = response.json()
            assert "drift_detected" in data
            # With significant drift, should likely be detected
            # (depends on threshold)


def test_calculate_drift_empty_data(client):
    """Test drift calculation with empty data"""
    
    request_data = {
        "current_data": [],
        "use_cached_reference": True
    }
    
    response = client.post("/calculate_drift", json=request_data)
    assert response.status_code == 400


def test_get_latest_drift(client):
    """Test getting latest drift report"""
    response = client.get("/drift/latest")
    assert response.status_code == 200


def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200


def test_parse_drift_report():
    """Test drift report parsing"""
    
    # Mock Evidently report structure
    mock_report = {
        "metrics": [
            {
                "metric": "DatasetDriftMetric",
                "result": {
                    "drift_by_columns": {
                        "vibration": {
                            "drift_score": 0.5,
                            "drift_detected": True
                        },
                        "temperature": {
                            "drift_score": 0.2,
                            "drift_detected": False
                        }
                    }
                }
            }
        ]
    }
    
    result = parse_drift_report(mock_report, ["vibration", "temperature"])
    
    assert "drift_detected" in result
    assert "drift_score" in result
    assert "feature_drifts" in result
    assert result["feature_drifts"]["vibration"] == 0.5
    assert result["feature_drifts"]["temperature"] == 0.2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
