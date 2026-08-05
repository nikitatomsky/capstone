"""
Tests for CORS (Cross-Origin Resource Sharing) middleware.

Validates that the FastAPI backend allows cross-origin requests from
the React SPA frontend (localhost:5173 for Vite dev server).
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_cors_headers_present_on_preflight():
    """Test CORS headers are present on OPTIONS preflight request."""
    response = client.options(
        "/api/assignments",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers


def test_cors_headers_present_on_actual_request():
    """Test CORS headers are present on actual API request."""
    response = client.get(
        "/api/assignments",
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_headers_present_on_health_check():
    """Test CORS headers are present on health check endpoint."""
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_cors_allows_frontend_on_port_5174():
    """Test CORS headers work for frontend running on port 5174."""
    response = client.get(
        "/api/assignments",
        headers={"Origin": "http://localhost:5174"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:5174"


def test_cors_preflight_for_port_5174():
    """Test CORS preflight works for port 5174."""
    response = client.options(
        "/api/assignments",
        headers={
            "Origin": "http://localhost:5174",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5174"


def test_cors_allows_alternative_react_port():
    """Test CORS allows requests from alternative React dev port (3000)."""
    response = client.get(
        "/api/assignments",
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_rejects_unauthorized_origin():
    """Test CORS rejects requests from non-whitelisted origins."""
    response = client.get(
        "/api/assignments",
        headers={"Origin": "http://malicious-site.com"},
    )
    # Request still succeeds but no CORS header should be present
    # (browser will block the response)
    assert response.status_code == 200
    # The CORS middleware should NOT include allow-origin for unauthorized origins
    # or it should not match the requested origin
    if "access-control-allow-origin" in response.headers:
        assert response.headers["access-control-allow-origin"] != "http://malicious-site.com"


def test_cors_credentials_allowed():
    """Test CORS allows credentials (cookies, authorization headers)."""
    response = client.get(
        "/api/assignments",
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200
    assert "access-control-allow-credentials" in response.headers
    assert response.headers["access-control-allow-credentials"] == "true"
