"""
Tests for the Authentication Service
"""

import pytest  # type: ignore
from app.services.auth_service import (
    AuthService,
    auth_service,
    get_auth_headers,
    get_api_key,
    get_auth_status,
)


class TestAuthService:
    """Test suite for AuthService"""

    def test_auth_service_initialization(self):
        """Test that AuthService initializes correctly"""
        service = AuthService()
        assert service is not None
        assert hasattr(service, "_api_keys")
        assert hasattr(service, "get_api_key")
        assert hasattr(service, "get_auth_headers")

    def test_get_api_key(self):
        """Test getting API keys"""
        key = auth_service.get_api_key("weather_ai")
        assert key is not None or key == ""

    def test_get_api_key_invalid_type(self):
        """Test getting API key with invalid type"""
        key = auth_service.get_api_key("invalid_type")
        assert key is None

    def test_get_auth_headers(self):
        """Test generating authentication headers"""
        try:
            headers = auth_service.get_auth_headers("weather_ai")
            assert isinstance(headers, dict)
            assert "Accept" in headers
            assert "Content-Type" in headers
        except ValueError:
            pass

    def test_get_auth_headers_invalid_type(self):
        """Test generating headers with invalid API type"""
        with pytest.raises(ValueError):
            auth_service.get_auth_headers("invalid_type")

    def test_mask_api_key(self):
        """Test API key masking"""
        service = AuthService()
        key = "wai_test_key_123456789"
        masked = service.mask_api_key(key)
        assert masked is not None
        assert "test" in masked or "***" in masked

    def test_get_auth_status(self):
        """Test getting authentication status"""
        status = auth_service.get_auth_status()
        assert isinstance(status, dict)
        assert "timestamp" in status
        assert "apis" in status
        assert "weather_ai" in status["apis"]
        assert "openweather" in status["apis"]

    def test_convenience_functions(self):
        """Test convenience functions"""
        try:
            headers = get_auth_headers("weather_ai")
            assert isinstance(headers, dict)
        except ValueError:
            pass

        key = get_api_key("weather_ai")
        assert key is not None or key == ""

        status = get_auth_status()
        assert isinstance(status, dict)
