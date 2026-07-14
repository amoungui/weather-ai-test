"""
Weather Service with WeatherAI as primary provider and OpenWeatherMap as fallback
"""

import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from enum import Enum

from app.config import settings
from app.services.auth_service import get_auth_headers

logger = logging.getLogger(__name__)


class WeatherUnits(str, Enum):
    METRIC = "metric"
    IMPERIAL = "imperial"


class WeatherService:
    """
    Weather Service with WeatherAI as primary provider
    """

    WEATHER_AI_BASE_URL = settings.weather_ai_url
    OPENWEATHER_BASE_URL = getattr(
        settings, "openweather_url", "https://api.openweathermap.org/data/2.5"
    )

    def __init__(self):
        self.client = None
        self._init_client()

        # Check which providers are available
        self.use_weather_ai = bool(settings.weather_ai_api_key)
        self.use_openweather = bool(settings.openweather_api_key)

        logger.info("Weather service initialized")
        logger.info(f"   WeatherAI: {'Enabled' if self.use_weather_ai else 'Disabled'}")
        logger.info(
            f"   OpenWeatherMap: {'Enabled' if self.use_openweather else 'Disabled'}"
        )

        if not self.use_weather_ai and not self.use_openweather:
            logger.warning(" No weather API providers configured!")

    def _init_client(self):
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
        Fetch weather data - tries WeatherAI first, falls back to OpenWeatherMap
        """

        self._validate_parameters(lat, lon, days, units)

        # Try WeatherAI first
        if self.use_weather_ai:
            try:
                logger.info(f"Fetching from WeatherAI: lat={lat}, lon={lon}")
                return await self._get_weather_weather_ai(
                    lat, lon, days, ai, units, lang
                )
            except Exception as e:
                logger.warning(f"WeatherAI failed: {str(e)}")
                if self.use_openweather:
                    logger.info("Falling back to OpenWeatherMap")
                else:
                    raise

        # Fallback to OpenWeatherMap
        if self.use_openweather:
            logger.info(f"Fetching from OpenWeatherMap: lat={lat}, lon={lon}")
            return await self._get_weather_openweather(lat, lon, days, units)

        raise Exception("No weather API providers available")

    async def _get_weather_weather_ai(
        self, lat: float, lon: float, days: int, ai: bool, units: str, lang: str
    ) -> Dict[str, Any]:
        """Fetch weather from WeatherAI API"""

        params = {
            "lat": lat,
            "lon": lon,
            "days": days,
            "ai": str(ai).lower(),
            "units": units,
            "lang": lang,
        }

        headers = get_auth_headers("weather_ai")

        try:
            response = await self.client.get(
                f"{self.WEATHER_AI_BASE_URL}/weather",
                params=params,
                headers=headers,
                follow_redirects=True,
            )

            if response.status_code == 503:
                raise Exception("WeatherAI service temporarily unavailable")

            response.raise_for_status()
            data = response.json()
            
            transformed_data = {
                "current": data.get("current", {}),
                "forecast": data.get("daily", []),  # Use 'daily'
                "location": {
                    "name": "WeatherAI Location",
                    "display_name": f"Lat: {lat}, Lon: {lon}",
                    "lat": lat,
                    "lon": lon
                },
                "ai_summary": data.get("ai_summary"),
                "timestamp": datetime.now().isoformat(),
                "rate_limit": {
                    "limit": response.headers.get("X-RateLimit-Limit", "N/A"),
                    "remaining": response.headers.get("X-RateLimit-Remaining", "N/A"),
                    "reset": response.headers.get("X-RateLimit-Reset", "N/A"),
                },
                "provider": "weather_ai",
                # Keep the raw data for reference
                "_raw": data
            }
            
            logger.info(f"✅ Weather data transformed: {len(transformed_data['forecast'])} forecast days")
            return transformed_data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise Exception("Invalid WeatherAI API key")
            elif e.response.status_code == 429:
                raise Exception("WeatherAI quota exceeded")
            elif e.response.status_code == 503:
                raise Exception("WeatherAI service unavailable")
            raise

    async def _get_weather_openweather(
        self, lat: float, lon: float, days: int, units: str
    ) -> Dict[str, Any]:
        """Fetch weather from OpenWeatherMap API (fallback)"""

        if not settings.openweather_api_key:
            raise Exception("OpenWeatherMap API key not configured")

        actual_days = min(days, 5)
        cnt = actual_days * 8

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

            response.raise_for_status()
            data = response.json()

            return self._transform_openweather_response(data, units, actual_days)

        except Exception as e:
            raise Exception(f"OpenWeatherMap error: {str(e)}")

    def _transform_openweather_response(
        self, data: Dict, units: str, days: int
    ) -> Dict:
        """Transform OpenWeatherMap response to consistent format"""

        city = data.get("city", {})
        forecasts = data.get("list", [])

        if not forecasts:
            raise Exception("No forecast data available")

        current = forecasts[0]

        daily_forecasts = []
        seen_dates = set()

        for forecast in forecasts:
            date = forecast["dt_txt"].split(" ")[0]
            if date not in seen_dates and len(daily_forecasts) < days:
                seen_dates.add(date)

                day_forecasts = [f for f in forecasts if f["dt_txt"].startswith(date)]

                if day_forecasts:
                    temp_max = max(f["main"]["temp_max"] for f in day_forecasts)
                    temp_min = min(f["main"]["temp_min"] for f in day_forecasts)
                    noon_forecast = next(
                        (f for f in day_forecasts if "12:00" in f["dt_txt"]),
                        day_forecasts[0],
                    )

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
                            "precipitation": 0,
                        }
                    )

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
                "visibility": current.get("visibility"),
                "icon": self._get_openweather_icon(current["weather"][0]["icon"]),
                "units": units,
            },
            "forecast": daily_forecasts,
            "location": {
                "name": city.get("name", "Unknown"),
                "country": city.get("country", ""),
                "display_name": f"{city.get('name', 'Unknown')}, {city.get('country', '')}",
                "lat": city.get("coord", {}).get("lat"),
                "lon": city.get("coord", {}).get("lon"),
            },
            "ai_summary": None,
            "timestamp": datetime.now().isoformat(),
            "rate_limit": {"limit": "N/A", "remaining": "N/A", "reset": "N/A"},
            "provider": "openweathermap",
        }

    def _get_openweather_icon(self, icon_code: str) -> str:
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
        if not -90 <= lat <= 90:
            raise ValueError(f"Invalid latitude: {lat}")
        if not -180 <= lon <= 180:
            raise ValueError(f"Invalid longitude: {lon}")
        if not 1 <= days <= 16:
            raise ValueError(f"Invalid days: {days}")
        if units not in ["metric", "imperial"]:
            raise ValueError(f"Invalid units: {units}")

    async def get_forecast(
        self, lat: float, lon: float, days: int = 7, units: str = "metric"
    ) -> Dict[str, Any]:
        """
        Fetch forecast data from WeatherAI API
        """
        params = {"lat": lat, "lon": lon, "days": days, "units": units}

        headers = get_auth_headers("weather_ai")

        try:
            response = await self.client.get(
                f"{self.WEATHER_AI_BASE_URL}/forecast",
                params=params,
                headers=headers,
                follow_redirects=True,
            )
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            logger.error(f"Error fetching forecast: {str(e)}")
            raise

    async def get_current_weather(
        self,
        lat: float,
        lon: float,
        units: str = "metric"
    ) -> Dict[str, Any]:
        """
        Fetch current weather from WeatherAI API
        """
        params = {
            "lat": lat,
            "lon": lon,
            "units": units
        }
        
        headers = get_auth_headers('weather_ai')
        
        try:
            response = await self.client.get(
                f"{self.WEATHER_AI_BASE_URL}/current",
                params=params,
                headers=headers,
                follow_redirects=True
            )
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            logger.error(f"Error fetching current weather: {str(e)}")
            raise
    
    async def get_usage(self) -> Dict[str, Any]:
        """Get usage data from WeatherAI"""
        if not self.use_weather_ai:
            return {
                "plan": "OpenWeatherMap (No usage tracking)",
                "requests_used": 0,
                "requests_limit": 0,
                "ai_requests_used": 0,
                "ai_requests_limit": 0,
                "provider": "openweathermap",
            }

        try:
            headers = get_auth_headers("weather_ai")
            response = await self.client.get(
                f"{self.WEATHER_AI_BASE_URL}/usage",
                headers=headers,
                follow_redirects=True,
            )
            response.raise_for_status()
            data = response.json()
            data["provider"] = "weather_ai"
            return data
        except Exception as e:
            logger.error(f"Error fetching usage: {str(e)}")
            return {"error": str(e), "provider": "weather_ai"}

    async def close(self):
        if self.client:
            await self.client.aclose()


# Create global instance
weather_service = WeatherService()


async def get_weather(lat, lon, days=7, ai=True, units="metric", lang="en"):
    return await weather_service.get_weather(lat, lon, days, ai, units, lang)


async def get_usage():
    return await weather_service.get_usage()

# ============================================
# Module-level functions
# ============================================

async def get_forecast(lat: float, lon: float, days: int = 7, units: str = "metric") -> Dict[str, Any]:
    """
    Convenience function to fetch forecast data
    """
    return await weather_service.get_forecast(lat, lon, days, units)

async def get_current_weather(lat: float, lon: float, units: str = "metric") -> Dict[str, Any]:
    """
    Convenience function to fetch current weather
    """
    return await weather_service.get_current_weather(lat, lon, units)

# Mettre à jour __all__
__all__ = [
    "WeatherService",
    "weather_service",
    "get_weather",
    "get_usage",
    "get_forecast",
    "get_current_weather",
    "WeatherUnits",
]