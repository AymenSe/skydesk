from fastapi.testclient import TestClient

from skydesk.api.main import app


def test_health_is_ok():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}