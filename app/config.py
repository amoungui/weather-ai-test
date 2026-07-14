"""
Application Configuration Module

This module manages all configuration settings for the application,
including environment variables, API keys, and application settings.
"""

import os
from typing import List, Union
from dotenv import load_dotenv
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# ============================================
# Helper Functions
# ============================================


def parse_cors_origins(value: str) -> List[str]:
    """
    Parse CORS origins from string or JSON format

    Args:
        value: String containing CORS origins (comma-separated or JSON array)

    Returns:
        List of allowed origins
    """
    if not value:
        return ["*"]

    if value == "*" or value == '["*"]':
        return ["*"]

    if value.startswith("[") and value.endswith("]"):
        try:
            import json

            result = json.loads(value)
            if isinstance(result, list):
                return result
        except:
            pass

    # Split by comma
    return [origin.strip() for origin in value.split(",") if origin.strip()]


def parse_bool(value: Union[str, bool]) -> bool:
    """
    Convert string to boolean

    Args:
        value: String or boolean value

    Returns:
        Boolean representation
    """
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("true", "1", "yes", "on", "enabled")


def mask_sensitive_value(value: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive values for display

    Args:
        value: The value to mask
        visible_chars: Number of characters to show at start and end

    Returns:
        Masked value
    """
    if not value:
        return "Not configured"

    if len(value) <= visible_chars * 2:
        return "***"

    prefix = value[:visible_chars]
    suffix = value[-visible_chars:]
    return f"{prefix}...{suffix}"


# ============================================
# Environment Variables
# ============================================

# WeatherAI Configuration
WEATHER_AI_API_KEY = os.getenv("WEATHER_AI_API_KEY", "")
WEATHER_AI_URL = os.getenv("WEATHER_AI_URL", "https://api.weather-ai.co/v1")

# OpenWeatherMap Configuration (fallback)
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_URL = os.getenv(
    "OPENWEATHER_URL", "https://api.openweathermap.org/data/2.5"
)

# Application Configuration
APP_ENV = os.getenv("APP_ENV", "development")
APP_DEBUG = parse_bool(os.getenv("APP_DEBUG", "true"))
APP_NAME = os.getenv("APP_NAME", "WeatherAI Integration")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# CORS Configuration
CORS_RAW = os.getenv("CORS_ORIGINS", "*")
CORS_ORIGINS = parse_cors_origins(CORS_RAW)

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv(
    "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# ============================================
# Settings Class for Compatibility
# ============================================


class Settings:
    """
    Settings class for backward compatibility with existing code
    """

    def __init__(self):
        # API Configuration
        self.weather_ai_api_key = WEATHER_AI_API_KEY
        self.weather_ai_url = WEATHER_AI_URL
        self.openweather_api_key = OPENWEATHER_API_KEY
        self.openweather_url = OPENWEATHER_URL

        # Application Configuration
        self.app_env = APP_ENV
        self.app_debug = APP_DEBUG
        self.app_name = APP_NAME
        self.app_version = APP_VERSION

        # Server Configuration
        self.host = HOST
        self.port = PORT

        # CORS Configuration
        self.cors_origins = CORS_ORIGINS

        # Logging Configuration
        self.log_level = LOG_LEVEL
        self.log_format = LOG_FORMAT


# Create global settings instance
settings = Settings()

# ============================================
# Validation and Startup Messages
# ============================================


def validate_configuration():
    """
    Validate the configuration settings

    Returns:
        bool: True if configuration is valid, False otherwise
    """
    logger.info("Validating configuration...")

    # Check if at least one API key is configured
    has_weather_ai = bool(WEATHER_AI_API_KEY)
    has_openweather = bool(OPENWEATHER_API_KEY)

    if not has_weather_ai and not has_openweather:
        logger.warning(" No API keys configured!")
        logger.warning(" Please configure at least one API key:")
        logger.warning(" WEATHER_AI_API_KEY (recommended)")
        logger.warning(" OPENWEATHER_API_KEY (fallback)")
        return False

    # Log configuration status
    logger.info("Configuration Status:")
    logger.info(f"   Application: {APP_NAME} v{APP_VERSION}")
    logger.info(f"   Environment: {APP_ENV}")
    logger.info(f"   Debug Mode: {APP_DEBUG}")
    logger.info(
        f"   WeatherAI API: {'Configured' if has_weather_ai else 'Not configured'}"
    )
    logger.info(
        f"   OpenWeather API: {'Configured' if has_openweather else 'Not configured'}"
    )
    logger.info(f"   CORS Origins: {CORS_ORIGINS}")
    logger.info(f"   Log Level: {LOG_LEVEL}")

    return True


# Run validation
validate_configuration()

# ============================================
# Exports
# ============================================

__all__ = [
    "settings",
    "WEATHER_AI_API_KEY",
    "WEATHER_AI_URL",
    "OPENWEATHER_API_KEY",
    "OPENWEATHER_URL",
    "APP_ENV",
    "APP_DEBUG",
    "APP_NAME",
    "APP_VERSION",
    "HOST",
    "PORT",
    "CORS_ORIGINS",
    "LOG_LEVEL",
    "LOG_FORMAT",
    "validate_configuration",
]
