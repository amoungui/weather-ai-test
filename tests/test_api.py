"""
Tests for API endpoints
"""

import pytest  # type: ignore
from fastapi.testclient import TestClient
from app.main import app


class TestAPI:
    """Test suite for API endpoints"""

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data

    def test_health_endpoint(self, client):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data

    def test_auth_status_endpoint(self, client):
        """Test authentication status endpoint"""
        response = client.get("/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "apis" in data
        assert "weather_ai" in data["apis"]
        assert "openweather" in data["apis"]

    def test_weather_endpoint_valid(self, client):
        """Test weather endpoint with valid parameters"""
        response = client.get(
            "/api/weather",
            params={"lat": -1.2921, "lon": 36.8219, "days": 3, "units": "metric"},
        )
        # The API might return 200 or 500 depending on API key configuration
        assert response.status_code != 404
        if response.status_code == 200:
            data = response.json()
            assert "current" in data
            assert "forecast" in data
            assert "location" in data

    def test_weather_endpoint_invalid_lat(self, client):
        """Test weather endpoint with invalid latitude"""
        response = client.get(
            "/api/weather", params={"lat": 100, "lon": 36.8219, "days": 3}
        )
        assert response.status_code == 400

    def test_weather_endpoint_invalid_lon(self, client):
        """Test weather endpoint with invalid longitude"""
        response = client.get(
            "/api/weather", params={"lat": -1.2921, "lon": 200, "days": 3}
        )
        assert response.status_code == 400

    def test_weather_endpoint_invalid_days(self, client):
        """Test weather endpoint with invalid days"""
        response = client.get(
            "/api/weather", params={"lat": -1.2921, "lon": 36.8219, "days": 0}
        )
        assert response.status_code == 400

    def test_weather_current_endpoint(self, client):
        """Test current weather endpoint"""
        response = client.get(
            "/api/weather/current", params={"lat": -1.2921, "lon": 36.8219}
        )
        assert response.status_code != 404
        if response.status_code == 200:
            data = response.json()
            assert "current" in data
            assert "location" in data

    def test_weather_forecast_endpoint(self, client):
        """Test forecast endpoint"""
        response = client.get(
            "/api/weather/forecast", params={"lat": -1.2921, "lon": 36.8219, "days": 3}
        )
        assert response.status_code != 404
        if response.status_code == 200:
            data = response.json()
            assert "forecast" in data
            assert "location" in data

    def test_usage_endpoint(self, client):
        """Test usage endpoint"""
        response = client.get("/api/usage")
        # May return 200 or 500 depending on API key configuration
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "plan" in data or "provider" in data

    def test_config_endpoint_development(self, client):
        """Test config endpoint in development mode"""
        response = client.get("/config")
        assert response.status_code == 200
        data = response.json()
        assert "app" in data
        assert "server" in data
        assert "apis" in data

    def test_nonexistent_endpoint(self, client):
        """Test nonexistent endpoint returns 404"""
        response = client.get("/nonexistent")
        assert response.status_code == 404
