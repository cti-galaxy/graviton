from fastapi.testclient import TestClient

from server import app

client = TestClient(app)


def test_roots_discovery():
    response = client.get("/taxii2")
    assert response.status_code == 200
