"""
Weather Routes for FastAPI
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime
import logging
from app.services.weather_service import (
    get_weather,
    get_usage,
    get_forecast,
    get_current_weather,
)
from app.services.weather_service import get_weather, get_usage

logger = logging.getLogger(__name__)

# Create router with prefix
router = APIRouter(prefix="/api", tags=["Weather"])


@router.get("/weather")
async def get_weather_endpoint(
    lat: float = Query(..., description="Latitude", ge=-90, le=90),
    lon: float = Query(..., description="Longitude", ge=-180, le=180),
    days: int = Query(7, description="Number of forecast days", ge=1, le=16),
    ai: bool = Query(True, description="Include AI summary"),
    units: str = Query(
        "metric", description="Units: metric or imperial", pattern="^(metric|imperial)$"
    ),
    lang: str = Query("en", description="Language code"),
):
    """
    Get current weather and forecast
    """
    logger.info(f"Weather request: lat={lat}, lon={lon}, days={days}, ai={ai}")

    try:
        weather_data = await get_weather(
            lat=lat, lon=lon, days=days, ai=ai, units=units, lang=lang
        )

        return JSONResponse(
            content=weather_data,
            headers={
                "X-RateLimit-Limit": str(
                    weather_data.get("rate_limit", {}).get("limit", "")
                ),
                "X-RateLimit-Remaining": str(
                    weather_data.get("rate_limit", {}).get("remaining", "")
                ),
                "X-RateLimit-Reset": str(
                    weather_data.get("rate_limit", {}).get("reset", "")
                ),
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_msg = str(e)
        if "API key" in error_msg.lower():
            raise HTTPException(status_code=401, detail=error_msg)
        elif "quota" in error_msg.lower() or "exceeded" in error_msg.lower():
            raise HTTPException(status_code=429, detail=error_msg)
        else:
            raise HTTPException(status_code=500, detail=error_msg)


@router.get("/usage")
async def get_usage_endpoint():
    """
    Get account usage statistics
    """
    try:
        usage_data = await get_usage()
        return usage_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weather/current")
async def get_current_weather(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    units: str = Query("metric", description="Units: metric or imperial"),
):
    """Get current weather only"""
    try:
        weather_data = await get_weather(
            lat=lat, lon=lon, days=1, ai=False, units=units
        )
        return {
            "current": weather_data["current"],
            "location": weather_data["location"],
            "timestamp": weather_data["timestamp"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast")
async def get_forecast_endpoint(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    days: int = Query(7, description="Number of forecast days", ge=1, le=16),
    units: str = Query("metric", description="Units: metric or imperial"),
):
    """Get forecast data only"""
    try:
        data = await get_forecast(lat, lon, days, units)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current")
async def get_current_weather_endpoint(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    units: str = Query("metric", description="Units: metric or imperial"),
):
    """Get current weather only"""
    try:
        data = await get_current_weather(lat, lon, units)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weather/forecast")
async def get_forecast(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    days: int = Query(7, description="Number of days", ge=1, le=16),
    units: str = Query("metric", description="Units: metric or imperial"),
):
    """Get forecast only"""
    try:
        weather_data = await get_weather(
            lat=lat, lon=lon, days=days, ai=False, units=units
        )
        return {
            "forecast": weather_data["forecast"],
            "location": weather_data["location"],
            "timestamp": weather_data["timestamp"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
