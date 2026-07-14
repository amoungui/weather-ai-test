"""
Pytest configuration and shared fixtures
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print(f"Project root: {project_root}")
print(f"Python path: {sys.path[0]}")

import pytest
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Load test environment variables
load_dotenv()

from app.main import app

@pytest.fixture
def client():
    """FastAPI TestClient fixture"""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def nairobi_coordinates():
    """Nairobi coordinates for testing"""
    return {"lat": -1.2921, "lon": 36.8219}

@pytest.fixture
def paris_coordinates():
    """Paris coordinates for testing"""
    return {"lat": 48.8566, "lon": 2.3522}

@pytest.fixture
def invalid_coordinates():
    """Invalid coordinates for testing error handling"""
    return {"lat": 100, "lon": 200}