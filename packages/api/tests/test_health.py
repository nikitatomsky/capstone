"""Tests for the health check endpoint."""


def test_health_check(client):
    """Test that the health endpoint returns a healthy status."""
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
