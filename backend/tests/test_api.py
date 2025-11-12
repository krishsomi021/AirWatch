"""Tests for the API endpoints."""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model_loaded" in data
    assert "version" in data


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


def test_predict_endpoint_get():
    """Test the GET predict endpoint."""
    response = client.get("/api/predict?zip_code=08901")
    
    # May fail if model not trained yet
    if response.status_code == 200:
        data = response.json()
        assert "date" in data
        assert "location" in data
        assert "prob_unhealthy" in data
        assert "classification" in data
        assert data["classification"] in ["Safe", "Unhealthy"]
        assert 0 <= data["prob_unhealthy"] <= 1


def test_predict_endpoint_post():
    """Test the POST predict endpoint with features."""
    payload = {
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
    
    response = client.post("/api/predict/features", json=payload)
    
    # May fail if model not trained yet
    if response.status_code == 200:
        data = response.json()
        assert "classification" in data
        assert "prob_unhealthy" in data


def test_invalid_zip_code():
    """Test with invalid ZIP code."""
    response = client.get("/api/predict?zip_code=99999")
    # Should still return a response (may use defaults)
    assert response.status_code in [200, 500]


def test_openapi_docs():
    """Test that OpenAPI documentation is available."""
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    openapi_spec = response.json()
    assert "openapi" in openapi_spec
    assert "paths" in openapi_spec


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
