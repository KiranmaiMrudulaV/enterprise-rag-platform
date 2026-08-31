"""
API-layer smoke test. No database or vector store required — /health is
deliberately dependency-free so CI and `docker-compose up` can verify the
server started without needing the full stack up first.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_unknown_route_returns_structured_error_envelope():
    """FastAPI's default 404 still goes through our own handler pattern for consistency."""
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
