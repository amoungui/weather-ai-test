from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

# import the configuration settings from the config module
from app.config import settings, APP_ENV, APP_DEBUG

# create FastAPI application instance
app = FastAPI(
    title="WeatherAI Application",
    description="This is a sample weatherAI application.",
    version="1.0.0",
    docs_url="/docs" if APP_DEBUG else None,  # disable docs in production
    redoc_url="/redoc" if APP_DEBUG else None  # disable redoc in production,
)

# add CORS middleware to allow cross-origin requests
app.add_middleware( 
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # allow all methods
    allow_headers=["*"],  # allow all headers
)

static_dir = "app/static" #os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# mount the static files directory to serve static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# define a root endpoint that returns a welcome message and application information
@app.get("/")
async def root():
    return {
        "message": f"Bienvenue sur {settings.app_name}",
        "version": settings.app_version,
        "environment": APP_ENV,
        "docs": "/docs" if APP_DEBUG else "Not available in production",
        "health": "/health",
        "configuration": {
            "weather_ai_configured": bool(settings.weather_ai_api_key),
            "openweather_configured": bool(settings.openweather_api_key),
            "environment": APP_ENV
        }
    }

# route for health check endpoint
@app.get("/health")
async def health_check():
    """
    Endpoint  to check the health of the application
    """
    import datetime

    # check if the required API keys are set in the environment variables   
    config_status = {
        "weather_ai": bool(settings.weather_ai_api_key), 
        "openweather": bool(settings.openweather_api_key),
        "environment": APP_ENV
    }


    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "configuration": config_status  
    }

@app.get("/config")
async def get_config():
    """
    Endpoint to get the current configuration of the application
    """
    if APP_ENV == "production":
            return {"error": "Configuration not available in production"}
    
    # hide the sensitive information
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "app_env": APP_ENV,
        "app_debug": APP_DEBUG,
        "host": settings.host,
        "port": settings.port,
        "log_level": settings.log_level,
        "cors_origins": settings.cors_origins,
        "weather_ai_configured": bool(settings.weather_ai_api_key),
        "openweather_configured": bool(settings.openweather_api_key)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host=settings.host, 
        port=settings.port,
        reload=APP_DEBUG,
        log_level=settings.log_level.lower()
    )