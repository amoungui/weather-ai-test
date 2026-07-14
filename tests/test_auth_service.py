#!/usr/bin/env python
"""
Test script for the Authentication Service

This script tests all functionality of the AuthService class
including key loading, header generation, and validation.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.services.auth_service import AuthService, auth_service, get_auth_headers, get_api_key, get_auth_status
from app.config import settings

def test_auth_service():
    """Test all functionality of the authentication service"""
    
    print("\n" + "="*60)
    print("TESTING AUTHENTICATION SERVICE")
    print("="*60)
    
    # Test 1: Service Initialization
    print("\nTest 1: Service Initialization")
    print("-" * 40)
    
    service = AuthService()
    print(f"AuthService initialized successfully")
    print(f"   API Keys loaded: {list(service._api_keys.keys())}")
    
    # Test 2: Get API Keys
    print("\nTest 2: Get API Keys")
    print("-" * 40)
    
    weather_ai_key = service.get_api_key('weather_ai')
    openweather_key = service.get_api_key('openweather')
    
    print(f"   WeatherAI API Key: {'Found' if weather_ai_key else 'Not found'}")
    print(f"   OpenWeather API Key: {'Found' if openweather_key else 'Not found'}")
    
    if weather_ai_key:
        print(f"   WeatherAI Key (masked): {service.mask_api_key(weather_ai_key)}")
    
    # Test 3: Generate Authentication Headers
    print("\nTest 3: Generate Authentication Headers")
    print("-" * 40)
    
    try:
        headers = service.get_auth_headers('weather_ai')
        print(f"WeatherAI Headers generated successfully:")
        for key, value in headers.items():
            if key == 'Authorization':
                print(f"   {key}: {value[:15]}...{value[-5:]}")
            else:
                print(f"   {key}: {value}")
    except ValueError as e:
        print(f"Error: {e}")
    
    # Test 4: API Key Validation
    print("\nTest 4: API Key Validation")
    print("-" * 40)
    
    for api_type in ['weather_ai', 'openweather']:
        is_valid, message = service.validate_api_key(api_type)
        status = "True" if is_valid else "false"
        print(f"   {api_type}: {status} {message}")
    
    # Test 5: Authentication Status
    print("\nTest 5: Authentication Status")
    print("-" * 40)
    
    status = service.get_auth_status()
    print(f"   Timestamp: {status['timestamp']}")
    for api_type, info in status['apis'].items():
        print(f"\n   {api_type}:")
        print(f"     Configured: {info['configured']}")
        print(f"     Valid: {info['valid']}")
        print(f"     Message: {info['message']}")
        if info['masked_key']:
            print(f"     Key: {info['masked_key']}")
    
    # Test 6: Convenience Functions
    print("\nTest 6: Convenience Functions")
    print("-" * 40)
    
    try:
        headers = get_auth_headers('weather_ai')
        print(f" get_auth_headers() works: {len(headers)} headers")
    except Exception as e:
        print(f"Error: {e}")
    
    key = get_api_key('weather_ai')
    print(f"   get_api_key(): {'Found' if key else 'Not found'}")
    
    status = get_auth_status()
    print(f"   get_auth_status(): {'Available' if status else 'Error'}")
    
    # Test 7: Configuration Integration
    print("\nTest 7: Configuration Integration")
    print("-" * 40)
    
    print(f"   APP_ENV: {settings.app_env}")
    print(f"   APP_DEBUG: {settings.app_debug}")
    print(f"   WeatherAI URL: {settings.weather_ai_url}")
    print(f"   CORS Origins: {settings.cors_origins}")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    # Check if authentication is properly configured
    has_weather_ai = bool(service.get_weather_ai_key())
    has_openweather = bool(service.get_openweather_key())
    
    if has_weather_ai or has_openweather:
        print("Authentication service is ready!")
        if has_weather_ai:
            print("   WeatherAI API is configured")
        if has_openweather:
            print("   OpenWeatherMap API is configured (fallback)")
    else:
        print("No API keys configured!")
        print("   Please configure at least one API key in your .env file")
        print("   For WeatherAI: WEATHER_AI_API_KEY=wai_your_key_here")
        print("   For OpenWeatherMap: OPENWEATHER_API_KEY=your_key_here")
    
    print("="*60 + "\n")
    
    return has_weather_ai or has_openweather

if __name__ == "__main__":
    success = test_auth_service()
    sys.exit(0 if success else 1)