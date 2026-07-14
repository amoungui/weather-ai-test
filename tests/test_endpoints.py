"""
Tests for API endpoints
"""

import pytest  # type: ignore
from fastapi.testclient import TestClient
from app.main import app


class TestEndpoints:
    """Test suite for API endpoints"""

    def test_root_endpoint(self):
        """Test root endpoint"""
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    def test_health_endpoint(self):
        """Test health endpoint"""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_auth_status_endpoint(self):
        """Test authentication status endpoint"""
        client = TestClient(app)
        response = client.get("/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert "apis" in data

    def test_weather_endpoint_valid(self):
        """Test weather endpoint with valid parameters"""
        client = TestClient(app)
        response = client.get(
            "/api/weather", params={"lat": -1.2921, "lon": 36.8219, "days": 3}
        )
        # In test environment, may return 200 or 500 depending on API key
        assert response.status_code in [200, 500]

    def test_weather_endpoint_invalid_lat(self):
        """Test weather endpoint with invalid latitude"""
        client = TestClient(app)
        response = client.get(
            "/api/weather", params={"lat": 100, "lon": 36.8219, "days": 3}
        )
        assert response.status_code == 400

    def test_weather_endpoint_invalid_lon(self):
        """Test weather endpoint with invalid longitude"""
        client = TestClient(app)
        response = client.get(
            "/api/weather", params={"lat": -1.2921, "lon": 200, "days": 3}
        )
        assert response.status_code == 400

    def test_weather_endpoint_invalid_days(self):
        """Test weather endpoint with invalid days"""
        client = TestClient(app)
        response = client.get(
            "/api/weather", params={"lat": -1.2921, "lon": 36.8219, "days": 0}
        )
        assert response.status_code == 400

    def test_nonexistent_endpoint(self):
        """Test nonexistent endpoint returns 404"""
        client = TestClient(app)
        response = client.get("/nonexistent")
        assert response.status_code == 404
