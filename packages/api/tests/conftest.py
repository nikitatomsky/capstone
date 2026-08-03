"""Pytest configuration and shared fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a FastAPI TestClient for testing."""
    return TestClient(app)
