"""
Dashboard Routes
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter()

# Setup templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Weather Dashboard
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Home page
    """
    return templates.TemplateResponse("index.html", {"request": request})
