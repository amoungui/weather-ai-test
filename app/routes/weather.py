"""
Weather Routes for FastAPI

This module defines the REST API endpoints for weather data,
including current weather, forecasts, and usage statistics.
"""

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime
import logging

from app.services.weather_service import get_weather, get_usage

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api",
    tags=["Weather"],
    responses={
        400: {"description": "Bad Request - Invalid parameters"},
        401: {"description": "Unauthorized - Invalid API key"},
        403: {"description": "Forbidden - Plan limitation"},
        429: {"description": "Too Many Requests - Quota exceeded"},
        500: {"description": "Internal Server Error"},
    },
)


@router.get("/weather")
async def get_weather_endpoint(
    lat: float = Query(
        ...,
        description="Latitude coordinate (-90 to 90)",
        example=[-1.2921],
        ge=-90,
        le=90,
    ),
    lon: float = Query(
        ...,
        description="Longitude coordinate (-180 to 180)",
        example=36.8219,
        ge=-180,
        le=180,
    ),
    days: int = Query(
        7, description="Number of forecast days (1-16 depending on plan)", ge=1, le=16
    ),
    ai: bool = Query(True, description="Include AI-generated weather summary"),
    units: str = Query(
        "metric",
        description="Units: 'metric' for Celsius, 'imperial' for Fahrenheit",
        pattern="^(metric|imperial)$",
    ),
    lang: str = Query(
        "en", description="Language code for AI summary (e.g., 'en', 'fr', 'es')"
    ),
):
    """
    Get current weather and forecast for a location

    This endpoint returns:
    - Current weather conditions
    - Multi-day forecast
    - AI-generated summary (if ai=true)
    - Location information
    - Rate limit status

    Example:
    """

    logger.info(f"Weather request: lat={lat}, lon={lon}, days={days}, ai={ai}")

    try:
        # Fetch weather data
        weather_data = await get_weather(
            lat=lat, lon=lon, days=days, ai=ai, units=units, lang=lang
        )

        # Extract rate limit headers
        rate_limit = weather_data.get("rate_limit", {})

        # Return response with rate limit headers
        return JSONResponse(
            content=weather_data,
            headers={
                "X-RateLimit-Limit": str(rate_limit.get("limit", "")),
                "X-RateLimit-Remaining": str(rate_limit.get("remaining", "")),
                "X-RateLimit-Reset": str(rate_limit.get("reset", "")),
            },
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Weather API error: {error_msg}")

        # Map error messages to appropriate status codes
        if "API key" in error_msg.lower():
            raise HTTPException(status_code=401, detail=error_msg)
        elif "plan" in error_msg.lower():
            raise HTTPException(status_code=403, detail=error_msg)
        elif "quota" in error_msg.lower() or "exceeded" in error_msg.lower():
            raise HTTPException(status_code=429, detail=error_msg)
        elif "invalid" in error_msg.lower():
            raise HTTPException(status_code=400, detail=error_msg)
        else:
            raise HTTPException(status_code=500, detail=error_msg)


@router.get("/usage")
async def get_usage_endpoint():
    """
    Get account usage statistics

    Returns:
    - requests_used: Number of requests used in current period
    - requests_limit: Monthly request limit
    - ai_requests_used: AI requests used
    - ai_requests_limit: AI request limit
    - period_start: Billing period start date
    - period_end: Billing period end date
    - plan: Current plan name
    - remaining: Remaining requests

    Example:

    """

    logger.info("Usage request")

    try:
        # Fetch usage data
        usage_data = await get_usage()

        return usage_data

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Usage API error: {error_msg}")

        if "API key" in error_msg.lower():
            raise HTTPException(status_code=401, detail=error_msg)
        else:
            raise HTTPException(status_code=500, detail=error_msg)


@router.get("/weather/current")
async def get_current_weather(
    lat: float = Query(..., description="Latitude", example=-1.2921),
    lon: float = Query(..., description="Longitude", example=36.8219),
    units: str = Query("metric", description="Units: metric or imperial"),
):
    """
    Get only current weather conditions (without forecast)

    This is a convenience endpoint that returns just the current
    weather conditions for a location.

    Example:
    """

    try:
        # Fetch full weather data
        weather_data = await get_weather(
            lat=lat,
            lon=lon,
            days=1,  # Only 1 day for current conditions
            ai=False,  # No AI summary for faster response
            units=units,
        )

        # Return only current weather
        return {
            "current": weather_data["current"],
            "location": weather_data["location"],
            "timestamp": weather_data["timestamp"],
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weather/forecast")
async def get_forecast(
    lat: float = Query(..., description="Latitude", example=-1.2921),
    lon: float = Query(..., description="Longitude", example=36.8219),
    days: int = Query(7, description="Number of days", ge=1, le=16),
    units: str = Query("metric", description="Units: metric or imperial"),
):
    """
    Get only forecast data (without AI summary)

    This endpoint returns only the forecast data for a location,
    which is faster and uses fewer AI credits.

    Example:
    """

    try:
        # Fetch weather data without AI
        weather_data = await get_weather(
            lat=lat, lon=lon, days=days, ai=False, units=units  # No AI summary
        )

        # Return only forecast
        return {
            "forecast": weather_data["forecast"],
            "location": weather_data["location"],
            "timestamp": weather_data["timestamp"],
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
