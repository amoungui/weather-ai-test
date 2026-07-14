"""
Main Application Entry Point

This module initializes the FastAPI application and configures
all routes, middleware, and services.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import os
import time
import logging
from datetime import datetime
from contextlib import asynccontextmanager

# Import configuration
from app.config import settings, APP_ENV, APP_DEBUG, APP_NAME, APP_VERSION, LOG_LEVEL

# Import authentication service
from app.services.auth_service import auth_service, get_auth_status
from app.routes import weather as weather_routes

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global variable for uptime tracking
start_time = time.time()

# ============================================
# Lifespan Manager
# ============================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle events

    This function handles startup and shutdown events,
    logging important information and performing initialization.
    """
    # Startup
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    logger.info(f"Environment: {APP_ENV}")
    logger.info(f"Debug Mode: {APP_DEBUG}")

    # Check authentication status
    auth_status = get_auth_status()
    logger.info("Authentication Status:")
    for api_type, status in auth_status["apis"].items():
        status_emoji = "True" if status["configured"] else "False"
        logger.info(f"   {status_emoji} {api_type}: {status['message']}")

    if (
        not auth_status["apis"]["weather_ai"]["configured"]
        and not auth_status["apis"]["openweather"]["configured"]
    ):
        logger.warning("No API keys configured! Application will not work properly.")
        logger.warning(
            "   Please configure WEATHER_AI_API_KEY or OPENWEATHER_API_KEY in .env"
        )

    yield

    # Shutdown
    logger.info(f"Shutting down {APP_NAME}")


# ============================================
# Create FastAPI Application
# ============================================

app = FastAPI(
    title=APP_NAME,
    description="""
    ## WeatherAI Integration
    
    Application integrating the WeatherAI API for weather data with AI summaries.
    
    ### Features:
    - Real-time weather and forecasts
    - AI-generated summaries (Gemini)
    - Account usage tracking
    - Multi-API support (WeatherAI + OpenWeatherMap fallback)
    
    ### Authentication:
    API keys are managed through the AuthService. Configure your keys in .env
    
    ### Available Endpoints:
    - `GET /` - Application information
    - `GET /health` - Health check and status
    - `GET /api/weather` - Weather data
    - `GET /api/usage` - Account usage
    - `GET /auth/status` - Authentication status
    - `GET /config` - Configuration (development only)
    """,
    version=APP_VERSION,
    docs_url="/docs" if APP_DEBUG else None,
    redoc_url="/redoc" if APP_DEBUG else None,
    lifespan=lifespan,
)

# Include weather routes
app.include_router(weather_routes.router)

# ============================================
# Middleware
# ============================================


# Middleware for response time tracking
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Add X-Process-Time header to all responses

    This middleware measures the time taken to process each request
    and adds it as a response header for monitoring.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Log request details
    logger.debug(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )

    return response


# Middleware for global error handling
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    """
    Global error handling middleware

    Catches all unhandled exceptions and returns formatted JSON responses.
    """
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(e) if APP_DEBUG else "An unexpected error occurred",
                "path": request.url.path,
                "timestamp": datetime.now().isoformat(),
            },
        )


# ============================================
# CORS Configuration
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        settings.cors_origins if isinstance(settings.cors_origins, list) else ["*"]
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Exception Handlers
# ============================================


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTP exceptions with consistent formatting
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
            "timestamp": datetime.now().isoformat(),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors with detailed information
    """
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "details": errors,
            "path": request.url.path,
            "timestamp": datetime.now().isoformat(),
        },
    )


# ============================================
# Routes
# ============================================


@app.get("/")
async def root():
    """
    Root endpoint - Main entry point
    """
    auth_status = get_auth_status()

    return {
        "message": f"Welcome to {APP_NAME}",
        "version": APP_VERSION,
        "environment": APP_ENV,
        "endpoints": {
            "docs": "/docs" if APP_DEBUG else "Not available",
            "health": "/health",
            "weather": "/api/weather?lat=-1.2921&lon=36.8219",
            "usage": "/api/usage",
            "auth_status": "/auth/status",
            "config": "/config" if APP_DEBUG else "Not available",
        },
        "authentication": {
            "weather_ai_configured": auth_status["apis"]["weather_ai"]["configured"],
            "openweather_configured": auth_status["apis"]["openweather"]["configured"],
            "has_valid_key": auth_status["apis"]["weather_ai"]["valid"]
            or auth_status["apis"]["openweather"]["valid"],
        },
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint with detailed status
    """
    auth_status = get_auth_status()

    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
        "environment": APP_ENV,
        "uptime": time.time() - start_time,
        "authentication": auth_status,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/auth/status")
async def authentication_status():
    """
    Get detailed authentication status for all configured APIs
    """
    return get_auth_status()


@app.get("/config")
async def get_config():
    """
    Display application configuration

    This endpoint is only available in development mode.
    In production, it returns a 403 Forbidden error.
    """
    if APP_ENV == "production":
        raise HTTPException(
            status_code=403, detail="Configuration not available in production"
        )

    from app.config import settings

    return {
        "app": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "environment": APP_ENV,
            "debug": APP_DEBUG,
            "log_level": LOG_LEVEL,
        },
        "server": {"host": settings.host, "port": settings.port},
        "cors": {"origins": settings.cors_origins},
        "apis": {
            "weather_ai": {
                "url": settings.weather_ai_url,
                "configured": bool(settings.weather_ai_api_key),
            },
            "openweather": {
                "url": settings.openweather_url,
                "configured": bool(settings.openweather_api_key),
            },
        },
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/test/auth")
async def test_authentication():
    """
    Test endpoint to verify authentication is working

    Returns the current authentication status and a test header.
    """
    try:
        from app.services.auth_service import get_auth_headers

        headers = get_auth_headers("weather_ai")

        return {
            "status": "success",
            "message": "Authentication is working",
            "headers": {
                "Authorization": headers.get("Authorization", "Not set")[:20] + "...",
                "Accept": headers.get("Accept", "Not set"),
            },
            "auth_status": get_auth_status(),
        }
    except ValueError as e:
        return {"status": "error", "message": str(e), "auth_status": get_auth_status()}


# ============================================
# Application Entry Point
# ============================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=APP_DEBUG,
        log_level=settings.log_level.lower(),
    )
