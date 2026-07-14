"""
Weather Service - Uses OpenWeatherMap as primary provider
"""

import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from enum import Enum

from app.config import settings

logger = logging.getLogger(__name__)


class WeatherUnits(str, Enum):
    METRIC = "metric"
    IMPERIAL = "imperial"


class WeatherService:
    """
    Weather Service using OpenWeatherMap API
    """

    OPENWEATHER_BASE_URL = getattr(
        settings, "openweather_url", "https://api.openweathermap.org/data/2.5"
    )

    def __init__(self):
        """Initialize the weather service"""
        self.client = None
        self._init_client()

        # Check OpenWeatherMap configuration
        self.use_openweather = bool(settings.openweather_api_key)

        logger.info("Weather service initialized (OpenWeatherMap)")
        logger.info(
            f"   OpenWeatherMap: {'Enabled' if self.use_openweather else 'Disabled'}"
        )

        if not self.use_openweather:
            logger.warning("OpenWeatherMap API key not configured!")

    def _init_client(self):
        """Initialize the HTTP client"""
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=100),
        )

    async def get_weather(
        self,
        lat: float,
        lon: float,
        days: int = 7,
        ai: bool = True,
        units: str = "metric",
        lang: str = "en",
    ) -> Dict[str, Any]:
        """
        Fetch weather data from OpenWeatherMap API

        Args:
            lat: Latitude (-90 to 90)
            lon: Longitude (-180 to 180)
            days: Number of forecast days (1-5 for free tier)
            ai: Ignored (OpenWeatherMap doesn't have AI)
            units: 'metric' or 'imperial'
            lang: Ignored

        Returns:
            Dictionary with weather data in consistent format
        """

        # Validate parameters
        self._validate_parameters(lat, lon, days, units)

        if not self.use_openweather:
            raise Exception(
                "OpenWeatherMap API key not configured. Please add OPENWEATHER_API_KEY to .env"
            )

        logger.info(f"Fetching from OpenWeatherMap: lat={lat}, lon={lon}")
        return await self._get_weather_openweather(lat, lon, days, units)

    async def _get_weather_openweather(
        self, lat: float, lon: float, days: int, units: str
    ) -> Dict[str, Any]:
        """Fetch weather from OpenWeatherMap API"""

        # OpenWeatherMap free tier limited to 5 days (40 forecasts)
        actual_days = min(days, 5)
        cnt = actual_days * 8  # 8 forecasts per day (every 3 hours)

        params = {
            "lat": lat,
            "lon": lon,
            "appid": settings.openweather_api_key,
            "units": "metric" if units == "metric" else "imperial",
            "cnt": min(cnt, 40),
        }

        try:
            response = await self.client.get(
                f"{self.OPENWEATHER_BASE_URL}/forecast",
                params=params,
                follow_redirects=True,
            )

            if response.status_code == 401:
                raise Exception("Invalid OpenWeatherMap API key")
            elif response.status_code == 429:
                raise Exception(
                    "OpenWeatherMap rate limit exceeded. Please try again later."
                )

            response.raise_for_status()
            data = response.json()

            return self._transform_openweather_response(data, units, actual_days)

        except httpx.HTTPStatusError as e:
            raise Exception(f"OpenWeatherMap error: {e.response.status_code}")
        except Exception as e:
            raise Exception(f"OpenWeatherMap error: {str(e)}")

    def _transform_openweather_response(
        self, data: Dict, units: str, days: int
    ) -> Dict:
        """
        Transform OpenWeatherMap response to consistent format
        """

        city = data.get("city", {})
        forecasts = data.get("list", [])

        if not forecasts:
            raise Exception("No forecast data available")

        # Current weather (first forecast)
        current = forecasts[0]

        # Get unit symbols
        temp_unit = "°C" if units == "metric" else "°F"
        speed_unit = "km/h" if units == "metric" else "mph"

        # Daily forecasts
        daily_forecasts = []
        seen_dates = set()

        for forecast in forecasts:
            date = forecast["dt_txt"].split(" ")[0]
            if date not in seen_dates and len(daily_forecasts) < days:
                seen_dates.add(date)

                # Get all forecasts for this day
                day_forecasts = [f for f in forecasts if f["dt_txt"].startswith(date)]

                if day_forecasts:
                    # Get min/max temps
                    temp_max = max(f["main"]["temp_max"] for f in day_forecasts)
                    temp_min = min(f["main"]["temp_min"] for f in day_forecasts)

                    # Get noon forecast (or first if no noon)
                    noon_forecast = next(
                        (f for f in day_forecasts if "12:00" in f["dt_txt"]),
                        day_forecasts[0],
                    )

                    # Calculate precipitation
                    rain = noon_forecast.get("rain", {}).get("3h", 0)
                    snow = noon_forecast.get("snow", {}).get("3h", 0)
                    precipitation = rain + snow

                    daily_forecasts.append(
                        {
                            "date": date,
                            "day_name": self._get_day_name(date),
                            "temp_max": round(temp_max),
                            "temp_min": round(temp_min),
                            "description": noon_forecast["weather"][0][
                                "description"
                            ].capitalize(),
                            "icon": self._get_openweather_icon(
                                noon_forecast["weather"][0]["icon"]
                            ),
                            "humidity": noon_forecast["main"]["humidity"],
                            "wind_speed": (
                                round(noon_forecast["wind"]["speed"] * 3.6)
                                if units == "metric"
                                else round(noon_forecast["wind"]["speed"])
                            ),
                            "precipitation": round(precipitation, 1),
                        }
                    )

        # Build response
        return {
            "current": {
                "temp": round(current["main"]["temp"]),
                "feels_like": round(current["main"]["feels_like"]),
                "description": current["weather"][0]["description"].capitalize(),
                "humidity": current["main"]["humidity"],
                "wind_speed": (
                    round(current["wind"]["speed"] * 3.6)
                    if units == "metric"
                    else round(current["wind"]["speed"])
                ),
                "wind_direction": current["wind"].get("deg"),
                "pressure": current["main"]["pressure"],
                "uv_index": None,
                "cloud_cover": current["clouds"]["all"],
                "visibility": current.get("visibility", "N/A"),
                "icon": self._get_openweather_icon(current["weather"][0]["icon"]),
                "units": units,
                "temp_unit": temp_unit,
                "speed_unit": speed_unit,
            },
            "forecast": daily_forecasts,
            "location": {
                "name": city.get("name", "Unknown"),
                "country": city.get("country", ""),
                "display_name": f"{city.get('name', 'Unknown')}, {city.get('country', '')}",
                "lat": city.get("coord", {}).get("lat"),
                "lon": city.get("coord", {}).get("lon"),
                "timezone": None,
            },
            "ai_summary": None,
            "timestamp": datetime.now().isoformat(),
            "rate_limit": {"limit": "N/A", "remaining": "N/A", "reset": "N/A"},
            "provider": "openweathermap",
        }

    def _get_openweather_icon(self, icon_code: str) -> str:
        """Convert OpenWeatherMap icon code to emoji"""
        icon_map = {
            "01d": "☀️",
            "01n": "🌙",
            "02d": "⛅",
            "02n": "☁️",
            "03d": "☁️",
            "03n": "☁️",
            "04d": "☁️",
            "04n": "☁️",
            "09d": "🌧️",
            "09n": "🌧️",
            "10d": "🌦️",
            "10n": "🌧️",
            "11d": "⛈️",
            "11n": "⛈️",
            "13d": "❄️",
            "13n": "❄️",
            "50d": "🌫️",
            "50n": "🌫️",
        }
        return icon_map.get(icon_code, "🌡️")

    def _get_day_name(self, date_str: str) -> str:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            return date.strftime("%A")
        except:
            return "Unknown"

    def _validate_parameters(self, lat: float, lon: float, days: int, units: str):
        """Validate request parameters"""
        if not -90 <= lat <= 90:
            raise ValueError(f"Invalid latitude: {lat}. Must be between -90 and 90")
        if not -180 <= lon <= 180:
            raise ValueError(f"Invalid longitude: {lon}. Must be between -180 and 180")
        if not 1 <= days <= 16:
            raise ValueError(f"Invalid days: {days}. Must be between 1 and 16")
        if units not in ["metric", "imperial"]:
            raise ValueError(f"Invalid units: {units}. Must be 'metric' or 'imperial'")

    async def get_usage(self) -> Dict[str, Any]:
        """Get usage data (not available for OpenWeatherMap)"""
        return {
            "plan": "OpenWeatherMap (Free Tier)",
            "requests_used": 0,
            "requests_limit": 0,
            "ai_requests_used": 0,
            "ai_requests_limit": 0,
            "period_start": None,
            "period_end": None,
            "provider": "openweathermap",
            "note": "Usage tracking not available for OpenWeatherMap free tier",
        }

    async def close(self):
        """Close the HTTP client"""
        if self.client:
            await self.client.aclose()
            logger.debug("HTTP client closed")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# ============================================
# Convenience Functions
# ============================================

# Create global instance
weather_service = WeatherService()


async def get_weather(
    lat: float,
    lon: float,
    days: int = 7,
    ai: bool = True,
    units: str = "metric",
    lang: str = "en",
) -> Dict[str, Any]:
    """
    Convenience function to fetch weather data from OpenWeatherMap

    Args:
        lat: Latitude
        lon: Longitude
        days: Number of forecast days (max 5 for free tier)
        ai: Ignored (OpenWeatherMap doesn't have AI)
        units: 'metric' or 'imperial'
        lang: Ignored

    Returns:
        Weather data dictionary
    """
    return await weather_service.get_weather(lat, lon, days, ai, units, lang)


async def get_usage() -> Dict[str, Any]:
    """Convenience function to fetch usage data"""
    return await weather_service.get_usage()


# Export
__all__ = [
    "WeatherService",
    "weather_service",
    "get_weather",
    "get_usage",
    "WeatherUnits",
]
