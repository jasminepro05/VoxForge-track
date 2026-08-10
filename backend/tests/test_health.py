from fastapi.testclient import TestClient
from app.main import app


def test_health_starts_without_external_credentials():
    """Health checks must not initialise Gemini or Qdrant."""
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
