"""
Pytest configuration and shared fixtures
"""

import pytest
from fastapi.testclient import TestClient
import os
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
