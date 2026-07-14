"""
Authentication Service for WeatherAI API Integration

This module handles all authentication-related functionality including:
- API key management
- Authentication header generation
- API key validation
- Secure key handling
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
    Authentication Service for handling API keys and authentication headers
    
    This service manages API keys for both WeatherAI and OpenWeatherMap APIs,
    providing secure access and validation mechanisms.
    """
    
    # Supported API types
    API_TYPES = {
        'weather_ai': {
            'env_key': 'WEATHER_AI_API_KEY',
            'prefix': 'wai_',
            'header_prefix': 'Bearer'
        },
        'openweather': {
            'env_key': 'OPENWEATHER_API_KEY',
            'prefix': None,
            'header_prefix': None
        }
    }
    
    def __init__(self):
        """Initialize the authentication service"""
        self._api_keys = {}
        self._load_api_keys()
        
    def _load_api_keys(self) -> None:
        """
        Load API keys from environment variables
        
        This method securely loads API keys from environment variables
        and stores them in memory for later use.
        """
        # Load WeatherAI API key
        weather_ai_key = os.getenv('WEATHER_AI_API_KEY', '')
        if weather_ai_key:
            self._api_keys['weather_ai'] = weather_ai_key
            logger.info("✅ WeatherAI API key loaded successfully")
        else:
            logger.warning("⚠️  WeatherAI API key not found in environment variables")
        
        # Load OpenWeatherMap API key (fallback)
        openweather_key = os.getenv('OPENWEATHER_API_KEY', '')
        if openweather_key:
            self._api_keys['openweather'] = openweather_key
            logger.info("OpenWeatherMap API key loaded successfully")
        else:
            logger.info("OpenWeatherMap API key not configured (optional)")
    
    def get_api_key(self, api_type: str = 'weather_ai') -> Optional[str]:
        """
        Get the API key for a specific API type
        
        Args:
            api_type: Type of API ('weather_ai' or 'openweather')
            
        Returns:
            The API key if found, None otherwise
        """
        if api_type not in self._api_keys:
            logger.warning(f"API type '{api_type}' not found in configuration")
            return None
        
        key = self._api_keys.get(api_type)
        if not key:
            logger.warning(f"No API key found for '{api_type}'")
            return None
            
        return key
    
    def get_auth_headers(self, api_type: str = 'weather_ai') -> Dict[str, str]:
        """
        Generate authentication headers for API requests
        
        Args:
            api_type: Type of API ('weather_ai' or 'openweather')
            
        Returns:
            Dictionary of headers for the API request
            
        Raises:
            ValueError: If the API key is not configured or invalid
        """
        if api_type not in self.API_TYPES:
            raise ValueError(f"Unsupported API type: {api_type}")
        
        api_config = self.API_TYPES[api_type]
        api_key = self.get_api_key(api_type)
        
        if not api_key:
            error_msg = f"API key not configured for {api_type}"
            logger.error(f"{error_msg}")
            raise ValueError(error_msg)
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # WeatherAI uses Bearer token authentication
        if api_type == 'weather_ai':
            headers['Authorization'] = f"Bearer {api_key}"
            logger.debug(f"Generated Bearer token for {api_type}")
        
        # OpenWeatherMap uses query parameter authentication
        elif api_type == 'openweather':
            # For OpenWeatherMap, key is passed as query param, not header
            headers['X-API-Key'] = api_key  # Fallback header for some endpoints
            logger.debug(f"Generated API key header for {api_type}")
        
        return headers
    
    def validate_api_key(self, api_type: str = 'weather_ai') -> Tuple[bool, str]:
        """
        Validate the API key format
        
        Args:
            api_type: Type of API ('weather_ai' or 'openweather')
            
        Returns:
            Tuple of (is_valid, message)
        """
        api_key = self.get_api_key(api_type)
        
        if not api_key:
            return False, f"API key not configured for {api_type}"
        
        # Validate WeatherAI API key format
        if api_type == 'weather_ai':
            # WeatherAI keys should start with 'wai_'
            if not api_key.startswith('wai_'):
                return False, "Invalid WeatherAI API key format. Should start with 'wai_'"
            
            # Minimum length check
            if len(api_key) < 10:
                return False, "API key too short. Should be at least 10 characters"
            
            return True, "WeatherAI API key validation successful"
        
        # Validate OpenWeatherMap API key format
        elif api_type == 'openweather':
            # OpenWeatherMap keys are alphanumeric, typically 32 characters
            if len(api_key) < 20:
                return False, "OpenWeatherMap API key too short"
            
            return True, "OpenWeatherMap API key validation successful"
        
        return False, f"Unsupported API type: {api_type}"
    
    def mask_api_key(self, api_key: str, visible_chars: int = 4) -> str:
        """
        Mask an API key for secure display
        
        Args:
            api_key: The API key to mask
            visible_chars: Number of characters to show at start and end
            
        Returns:
            Masked API key (e.g., 'wai_****...****xyz')
        """
        if not api_key:
            return "Not configured"
        
        if len(api_key) <= visible_chars * 2:
            return "***"
        
        prefix = api_key[:visible_chars]
        suffix = api_key[-visible_chars:]
        masked_length = len(api_key) - (visible_chars * 2)
        
        return f"{prefix}{'*' * min(masked_length, 8)}...{suffix}"
    
    def get_auth_status(self) -> Dict[str, any]:
        """
        Get the current authentication status
        
        Returns:
            Dictionary with authentication status for all configured APIs
        """
        status = {
            'timestamp': datetime.now().isoformat(),
            'apis': {}
        }
        
        for api_type in self.API_TYPES:
            api_key = self.get_api_key(api_type)
            is_valid, message = self.validate_api_key(api_type) if api_key else (False, "Not configured")
            
            status['apis'][api_type] = {
                'configured': bool(api_key),
                'valid': is_valid,
                'message': message,
                'masked_key': self.mask_api_key(api_key) if api_key else None
            }
        
        return status
    
    def get_weather_ai_key(self) -> Optional[str]:
        """Convenience method to get WeatherAI API key"""
        return self.get_api_key('weather_ai')
    
    def get_openweather_key(self) -> Optional[str]:
        """Convenience method to get OpenWeatherMap API key"""
        return self.get_api_key('openweather')
    
    def is_weather_ai_configured(self) -> bool:
        """Check if WeatherAI API is configured"""
        return bool(self.get_weather_ai_key())
    
    def is_openweather_configured(self) -> bool:
        """Check if OpenWeatherMap API is configured"""
        return bool(self.get_openweather_key())

# Create a global instance of the authentication service
auth_service = AuthService()

# Convenience functions for easier import
def get_auth_headers(api_type: str = 'weather_ai') -> Dict[str, str]:
    """Convenience function to get authentication headers"""
    return auth_service.get_auth_headers(api_type)

def get_api_key(api_type: str = 'weather_ai') -> Optional[str]:
    """Convenience function to get API key"""
    return auth_service.get_api_key(api_type)

def get_auth_status() -> Dict[str, any]:
    """Convenience function to get authentication status"""
    return auth_service.get_auth_status()

# Export commonly used functions and classes
__all__ = [
    'AuthService',
    'auth_service',
    'get_auth_headers',
    'get_api_key',
    'get_auth_status'
]