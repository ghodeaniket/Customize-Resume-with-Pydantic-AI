"""Tests for the health check endpoint."""
from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """Test health check endpoint.
    
    Args:
        client: Test client
    """
    # Make request to health check endpoint
    response = client.get("/health")
    
    # Check response status code
    assert response.status_code == 200
    
    # Check response data
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "uptime" in data
    assert isinstance(data["uptime"], float)
