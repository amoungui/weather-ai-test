from typing import Optional, List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# load environment variables since the file .env
load_dotenv()

class Settings(BaseSettings):
    """
    Configuration of the application with validation of environment variables.
    """
    
    # Configuration WeatherAI
    weather_ai_api_key: str = Field(
        default="",
        description="API key for WeatherAI"
    )
    
    weather_ai_url: str = Field(
        default="https://api.weather-ai.co/v1",
        description="Base URL for the WeatherAI API"
    )
    
    # Configuration OpenWeatherMap (fallback)
    openweather_api_key: str = Field(
        default="",
        description="API key for OpenWeatherMap (fallback)"
    )
    
    # Configuration of the application
    app_env: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )
    
    app_debug: bool = Field(
        default=True,
        description="Debug mode: True for development, False for production"
    )
    
    app_name: str = Field(
        default="WeatherAI Integration",
        description="Name of the application"
    )
    
    app_version: str = Field(
        default="1.0.0",
        description="Version of the application"
    )
    
    # Configuration of the server
    host: str = Field(
        default="0.0.0.0",
        description="Host to listen on"
    )
    
    port: int = Field(
        default=8000,
        description="Port to listen on"
    )
    
    # Configuration CORS
    cors_origins: Union[str, List[str]] = Field(
        default="*",
        description="Origins authorized for CORS (separated by commas or '*' for all)"
    )
    
    # Configuration of the logging
    log_level: str = Field(
        default="INFO",
        description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Convert the CSV string to a list"""
        if v is None:
            return ["*"]
        if isinstance(v, str):
            # If it's "*", return ["*"]
            if v == "*" or v == '["*"]':
                return ["*"]
            # If it's a JSON list, parse it
            if v.startswith('[') and v.endswith(']'):
                try:
                    import json
                    return json.loads(v)
                except:
                    pass
            # Else, split by comma
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        return ["*"]
    
    @field_validator("app_debug", mode="before")
    @classmethod
    def parse_bool(cls, v):
        """Convert the string values to booleans"""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore the extra variables

# Create a global instance of the settings
try:
    settings = Settings()
    print("Configuration loaded successfully")
except Exception as e:
    print(f"Configuration error: {e}")
    # Create a default configuration in case of an error
    settings = Settings(
        weather_ai_api_key="",
        weather_ai_url="https://api.weather-ai.co/v1",
        app_env="development",
        app_debug=True,
        cors_origins=["*"]
    )

# Export the important variables for easy access
WEATHER_AI_API_KEY = settings.weather_ai_api_key
WEATHER_AI_URL = settings.weather_ai_url
OPENWEATHER_API_KEY = settings.openweather_api_key
APP_ENV = settings.app_env
APP_DEBUG = settings.app_debug
APP_NAME = settings.app_name
APP_VERSION = settings.app_version
HOST = settings.host
PORT = settings.port
CORS_ORIGINS = settings.cors_origins if isinstance(settings.cors_origins, list) else [settings.cors_origins]
LOG_LEVEL = settings.log_level

# Function for validation
def validate_settings():
    """
    Validates that the critical configurations are present.
    """
    if settings.app_env == "production":
        if not settings.weather_ai_api_key:
            print("ATTENTION: WEATHER_AI_API_KEY is required in production")
    
    if not settings.weather_ai_api_key:
        print("WeatherAI API Key not configured - using OpenWeatherMap as fallback")
    
    return True

# Validate at startup
validate_settings()