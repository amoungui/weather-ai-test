#!/usr/bin/env python
"""
quick script to test the configuration
"""

from app.config import settings, validate_settings


def test_config():
    print("🔧 Test of the configuration...")

    # Display the settings (without the complete keys)
    print(f"✅ App: {settings.app_name} v{settings.app_version}")
    print(f"✅ Environment: {settings.app_env}")
    print(f"✅ WeatherAI URL: {settings.weather_ai_url}")
    print(
        f"✅ WeatherAI Key: {'Configured' if settings.weather_ai_api_key else 'Not configured'}"
    )
    print(
        f"✅ OpenWeather Key: {'Configured' if settings.openweather_api_key else 'Not configured'}"
    )
    print(f"✅ CORS Origins: {settings.cors_origins}")
    print(f"✅ Log Level: {settings.log_level}")

    # Verify that the variables are accessible
    try:
        from app.config import WEATHER_AI_API_KEY, APP_ENV

        print(
            f"✅ Direct import - WeatherAI Key: {'OK' if WEATHER_AI_API_KEY else 'Not configured'}"
        )
        print(f"✅ Direct import - APP_ENV: {APP_ENV}")
    except ImportError as e:
        print(f"❌ Error importing variables: {e}")

    print("\n✅ Test completed successfully!")


if __name__ == "__main__":
    test_config()
