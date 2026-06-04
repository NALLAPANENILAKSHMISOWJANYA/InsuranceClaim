"""
Insurance Claim Pre-Assurance – Health Endpoint Tests
"""
from fastapi.testclient import TestClient


def test_health_returns_healthy(client: TestClient) -> None:
    """Health endpoint must return 200 with status=healthy when DB is connected."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "version" in data
    assert "timestamp" in data


def test_health_contains_app_name(client: TestClient) -> None:
    """Health response must include the application name."""
    response = client.get("/health")
    data = response.json()
    assert data["app_name"] == "Insurance Claim Pre-Assurance"
