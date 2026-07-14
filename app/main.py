"""
Main Application Entry Point

This module initializes the FastAPI application and configures
all routes, middleware, and services.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
import os
from fastapi.staticfiles import StaticFiles
import time
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

# Import configuration
from app.config import settings, APP_ENV, APP_DEBUG, APP_NAME, APP_VERSION, LOG_LEVEL

# Import authentication service
from app.services.auth_service import auth_service, get_auth_status

# Import weather routes
from app.routes import weather as weather_routes

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global variable for uptime tracking
start_time = time.time()

# Setup templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# ============================================
# Lifespan Manager
# ============================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle events
    """
    # Startup
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    logger.info(f"Environment: {APP_ENV}")
    logger.info(f"Debug Mode: {APP_DEBUG}")

    # Check authentication status
    auth_status = get_auth_status()
    logger.info("Authentication Status:")
    for api_type, status in auth_status["apis"].items():
        status_emoji = "true" if status["configured"] else "false"
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
    logger.info(f" Shutting down {APP_NAME}")


# ============================================
# Create FastAPI Application
# ============================================

app = FastAPI(
    title=APP_NAME,
    description="""
    ## 🌤️ WeatherAI Integration
    
    Application integrating weather APIs for weather data.
    
    ### Features:
    - Real-time weather and forecasts
    - Account usage tracking
    - Multi-API support (WeatherAI + OpenWeatherMap fallback)
    
    ### Available Endpoints:
    - `GET /` - Home page
    - `GET /dashboard` - Weather dashboard
    - `GET /health` - Health check
    - `GET /api/weather` - Weather data
    - `GET /api/weather/current` - Current weather only
    - `GET /api/weather/forecast` - Forecast only
    - `GET /api/usage` - Account usage
    - `GET /auth/status` - Authentication status
    """,
    version=APP_VERSION,
    docs_url="/docs" if APP_DEBUG else None,
    redoc_url="/redoc" if APP_DEBUG else None,
    lifespan=lifespan,
)

# ============================================
# Static Files
# ============================================

# Serve static files from the 'static' directory at project root
static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
    print(f"📁 Created static directory: {static_dir}")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
print(f"✅ Static files served from: /{static_dir}")

# ============================================
# Middleware
# ============================================


# Middleware for response time tracking
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Add X-Process-Time header to all responses
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
# Include Routers
# ============================================

# Include weather routes
app.include_router(weather_routes.router)

# ============================================
# HTML Routes (Dashboard)
# ============================================


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Home page
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Weather Dashboard
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})


# ============================================
# API Routes
# ============================================


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
    Display application configuration (development only)
    """
    if APP_ENV == "production":
        raise HTTPException(
            status_code=403, detail="Configuration not available in production"
        )

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
