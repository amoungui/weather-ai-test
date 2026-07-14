"""
Main Application Entry Point
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
import os
import time
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

# Import configuration
from app.config import settings, APP_ENV, APP_DEBUG, APP_NAME, APP_VERSION, LOG_LEVEL

# Import authentication service
from app.services.auth_service import auth_service, get_auth_status

# ✅ IMPORT DES ROUTES - CORRIGÉ
from app.routes import weather as weather_routes

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
    """Manage application lifecycle events"""
    logger.info(f"🚀 Starting {APP_NAME} v{APP_VERSION}")
    logger.info(f"📊 Environment: {APP_ENV}")
    logger.info(f"🔧 Debug Mode: {APP_DEBUG}")
    
    # Check authentication status
    auth_status = get_auth_status()
    logger.info("🔐 Authentication Status:")
    for api_type, status in auth_status['apis'].items():
        status_emoji = "✅" if status['configured'] else "❌"
        logger.info(f"   {status_emoji} {api_type}: {status['message']}")
    
    # ✅ Afficher les routes enregistrées
    logger.info("📡 Registered routes:")
    for route in app.routes:
        logger.info(f"   {route.methods if hasattr(route, 'methods') else 'N/A'} {route.path}")
    
    yield
    
    logger.info(f"👋 Shutting down {APP_NAME}")

# ============================================
# Create FastAPI Application
# ============================================

app = FastAPI(
    title=APP_NAME,
    description="Weather API Integration",
    version=APP_VERSION,
    docs_url="/docs" if APP_DEBUG else None,
    redoc_url="/redoc" if APP_DEBUG else None,
    lifespan=lifespan
)

# ============================================
# Static Files
# ============================================

static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ============================================
# Middleware
# ============================================

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.debug(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    return response

# ============================================
# CORS Configuration
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if isinstance(settings.cors_origins, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Exception Handlers
# ============================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
            "timestamp": datetime.now().isoformat()
        }
    )

# ============================================
# ✅ INCLUDE ROUTERS - CORRIGÉ
# ============================================

app.include_router(weather_routes.router)
logger.info("✅ Weather routes registered")

# ============================================
# HTML Routes
# ============================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# ============================================
# API Routes
# ============================================

@app.get("/health")
async def health_check():
    auth_status = get_auth_status()
    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
        "environment": APP_ENV,
        "uptime": time.time() - start_time,
        "authentication": auth_status,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/auth/status")
async def authentication_status():
    return get_auth_status()

@app.get("/config")
async def get_config():
    if APP_ENV == "production":
        raise HTTPException(status_code=403, detail="Configuration not available in production")
    return {
        "app": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "environment": APP_ENV,
            "debug": APP_DEBUG,
            "log_level": LOG_LEVEL
        },
        "server": {
            "host": settings.host,
            "port": settings.port
        },
        "cors": {"origins": settings.cors_origins},
        "apis": {
            "weather_ai": {
                "url": settings.weather_ai_url,
                "configured": bool(settings.weather_ai_api_key)
            },
            "openweather": {
                "url": settings.openweather_url,
                "configured": bool(settings.openweather_api_key)
            }
        },
        "timestamp": datetime.now().isoformat()
    }

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
        log_level=settings.log_level.lower()
    )