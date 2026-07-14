"""
Authentication Service for WeatherAI API Integration
"""

import os
import logging
from typing import Optional, Dict, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class AuthService:
    """
    Authentication Service for handling API keys
    """

    API_TYPES = {
        "weather_ai": {
            "env_key": "WEATHER_AI_API_KEY",
            "prefix": "wai_",
            "header_prefix": "Bearer",
        },
        "openweather": {
            "env_key": "OPENWEATHER_API_KEY",
            "prefix": None,
            "header_prefix": None,
        },
    }

    def __init__(self):
        """Initialize the authentication service"""
        self._api_keys = {}
        self._load_api_keys()

    def _load_api_keys(self) -> None:
        """Load API keys from environment variables"""
        # Load WeatherAI API key
        weather_ai_key = os.getenv("WEATHER_AI_API_KEY", "")
        if weather_ai_key:
            self._api_keys["weather_ai"] = weather_ai_key
            logger.info("WeatherAI API key loaded successfully")
        else:
            # Use test key in CI environment if available
            test_key = os.getenv("WEATHER_AI_API_KEY")
            if test_key:
                self._api_keys["weather_ai"] = test_key
                logger.info("WeatherAI API key loaded from environment")
            else:
                logger.warning("WeatherAI API key not found")
                self._api_keys["weather_ai"] = None

        # Load OpenWeatherMap API key
        openweather_key = os.getenv("OPENWEATHER_API_KEY", "")
        if openweather_key:
            self._api_keys["openweather"] = openweather_key
            logger.info("OpenWeatherMap API key loaded successfully")
        else:
            # Use test key in CI environment if available
            test_key = os.getenv("OPENWEATHER_API_KEY")
            if test_key:
                self._api_keys["openweather"] = test_key
                logger.info("OpenWeatherMap API key loaded from environment")
            else:
                logger.info("OpenWeatherMap API key not configured")
                self._api_keys["openweather"] = None

    def get_api_key(self, api_type: str = "weather_ai") -> Optional[str]:
        """
        Get the API key for a specific API type

        Args:
            api_type: Type of API ('weather_ai' or 'openweather')

        Returns:
            The API key if found, None otherwise
        """
        if api_type not in self._api_keys:
            return None

        return self._api_keys.get(api_type)

    def get_auth_headers(self, api_type: str = "weather_ai") -> Dict[str, str]:
        """
        Generate authentication headers for API requests
        """
        if api_type not in self.API_TYPES:
            raise ValueError(f"Unsupported API type: {api_type}")

        api_key = self.get_api_key(api_type)

        if not api_key:
            error_msg = f"API key not configured for {api_type}"
            logger.error(f"{error_msg}")
            raise ValueError(error_msg)

        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        if api_type == "weather_ai":
            headers["Authorization"] = f"Bearer {api_key}"
            logger.debug(f"Generated Bearer token for {api_type}")

        return headers

    def validate_api_key(self, api_type: str = "weather_ai") -> Tuple[bool, str]:
        """Validate the API key format"""
        api_key = self.get_api_key(api_type)

        if not api_key:
            return False, f"API key not configured for {api_type}"

        if api_type == "weather_ai":
            if not api_key.startswith("wai_"):
                return (
                    False,
                    "Invalid WeatherAI API key format. Should start with 'wai_'",
                )
            if len(api_key) < 10:
                return False, "API key too short"
            return True, "WeatherAI API key validation successful"

        elif api_type == "openweather":
            if len(api_key) < 20:
                return False, "OpenWeatherMap API key too short"
            return True, "OpenWeatherMap API key validation successful"

        return False, f"Unsupported API type: {api_type}"

    def mask_api_key(self, api_key: str, visible_chars: int = 4) -> str:
        """Mask an API key for secure display"""
        if not api_key:
            return "Not configured"

        if len(api_key) <= visible_chars * 2:
            return "***"

        prefix = api_key[:visible_chars]
        suffix = api_key[-visible_chars:]
        masked_length = len(api_key) - (visible_chars * 2)

        return f"{prefix}{'*' * min(masked_length, 8)}...{suffix}"

    def get_auth_status(self) -> Dict[str, any]:
        """Get the current authentication status"""
        status = {"timestamp": datetime.now().isoformat(), "apis": {}}

        for api_type in self.API_TYPES:
            api_key = self.get_api_key(api_type)
            is_valid, message = (
                self.validate_api_key(api_type)
                if api_key
                else (False, "Not configured")
            )

            status["apis"][api_type] = {
                "configured": bool(api_key),
                "valid": is_valid,
                "message": message,
                "masked_key": self.mask_api_key(api_key) if api_key else None,
            }

        return status

    def is_weather_ai_configured(self) -> bool:
        """Check if WeatherAI API is configured"""
        return bool(self.get_weather_ai_key())

    def is_openweather_configured(self) -> bool:
        """Check if OpenWeatherMap API is configured"""
        return bool(self.get_openweather_key())


# Create a global instance
auth_service = AuthService()


# Convenience functions
def get_auth_headers(api_type: str = "weather_ai") -> Dict[str, str]:
    return auth_service.get_auth_headers(api_type)


def get_api_key(api_type: str = "weather_ai") -> Optional[str]:
    return auth_service.get_api_key(api_type)


def get_auth_status() -> Dict[str, any]:
    return auth_service.get_auth_status()


__all__ = [
    "AuthService",
    "auth_service",
    "get_auth_headers",
    "get_api_key",
    "get_auth_status",
]
