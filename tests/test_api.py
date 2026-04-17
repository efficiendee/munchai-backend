import os

import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB", "munchai_test")
os.environ.setdefault("API_KEY", "change-me")

from app.db_mongo import ensure_indexes  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def clean_db() -> None:
    client = MongoClient(os.environ["MONGODB_URI"])
    db = client[os.environ["MONGODB_DB"]]
    db.users.delete_many({})
    db.recipes.delete_many({})
    ensure_indexes()
    yield
    db.users.delete_many({})
    db.recipes.delete_many({})
    client.close()


client = TestClient(app)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200


def test_user_crud_and_unique_email_hash() -> None:
    payload = {"username": "dave", "email": "dave@example.com", "password": "supersecret1"}
    r = client.post("/api/v1/users", json=payload, headers={"x-api-key": "change-me"})
    assert r.status_code == 201
    user_id = r.json()["id"]

    r2 = client.post("/api/v1/users", json=payload, headers={"x-api-key": "change-me"})
    assert r2.status_code == 409

    r3 = client.get(f"/api/v1/users/{user_id}", headers={"x-api-key": "change-me"})
    assert r3.status_code == 200
    assert r3.json()["username"] == "dave"
    assert r3.json()["verified"] is False


def test_recipe_crud() -> None:
    recipe = {
        "title": "Test Recipe",
        "description": "desc",
        "ingredients": ["a", "b"],
        "steps": ["s1", "s2"],
        "minutes": 10,
        "difficulty": "Easy",
        "image_url": "https://example.com/i.png",
        "tags": ["fast"],
    }

    create = client.post("/api/v1/recipes", json=recipe, headers={"x-api-key": "change-me"})
    assert create.status_code == 201
    rid = create.json()["id"]

    list_r = client.get("/api/v1/recipes", headers={"x-api-key": "change-me"})
    assert list_r.status_code == 200
    assert len(list_r.json()) == 1

    patch = client.patch(
        f"/api/v1/recipes/{rid}",
        json={"minutes": 12},
        headers={"x-api-key": "change-me"},
    )
    assert patch.status_code == 200
    assert patch.json()["minutes"] == 12

    delete = client.delete(f"/api/v1/recipes/{rid}", headers={"x-api-key": "change-me"})
    assert delete.status_code == 204
