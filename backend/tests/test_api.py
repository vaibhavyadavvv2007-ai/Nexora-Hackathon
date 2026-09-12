from starlette.testclient import TestClient


def test_health_check_endpoint(test_client: TestClient):
    """Verify GET /health responds with 200 and {'status': 'ok'}."""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
