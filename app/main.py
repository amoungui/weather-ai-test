from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

# create FastAPI application instance
app = FastAPI(
    title="WeatherAI Application",
    description="This is a sample weatherAI application.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
        "message": "Welcome to the WeatherAI Application!",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# route for health check endpoint
@app.get("/health")
async def health_check():
    """
    Endpoint de vérification de la santé de l'application
    """
    return {
        "status": "healthy",
        "service": "WeatherAI Integration",
        "timestamp": str(__import__('datetime').datetime.now())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000,
        reload=True
    )