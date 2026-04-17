from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_recipes_requires_api_key() -> None:
    r = client.get("/api/v1/recipes")
    assert r.status_code == 401


def test_recipes_with_api_key() -> None:
    r = client.get("/api/v1/recipes", headers={"x-api-key": "change-me"})
    assert r.status_code == 200
    assert len(r.json()) >= 1
