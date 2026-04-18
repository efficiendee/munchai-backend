import os
import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB", "munchai_test")
os.environ.setdefault("TOKEN_TTL_HOURS", "24")

from app.db_mongo import ensure_indexes  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def clean_db() -> None:
    client = MongoClient(os.environ["MONGODB_URI"])
    db = client[os.environ["MONGODB_DB"]]
    db.users.delete_many({})
    db.recipes.delete_many({})
    db.sessions.delete_many({})
    ensure_indexes()
    yield
    db.users.delete_many({})
    db.recipes.delete_many({})
    db.sessions.delete_many({})
    client.close()


client = TestClient(app)


def _register_verify_login(email: str = "dave@example.com") -> tuple[str, str]:
    payload = {
        "username": "dave",
        "email": email,
        "password": "supersecret1",
        "taste_profile": "Loves umami, spicy and quick meals",
    }
    created = client.post("/api/v1/users", json=payload)
    assert created.status_code == 201
    user_id = created.json()["id"]

    # login blocked until verified
    blocked = client.post("/api/v1/auth/login", json={"email": email, "password": payload["password"]})
    assert blocked.status_code == 401

    verify = client.post("/api/v1/auth/verify-account", json={"email": email})
    assert verify.status_code == 204

    login = client.post("/api/v1/auth/login", json={"email": email, "password": payload["password"]})
    assert login.status_code == 200
    token = login.json()["token"]
    return user_id, token


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200


def test_user_email_unique_and_taste_profile() -> None:
    payload = {
        "username": "dave",
        "email": "dave@example.com",
        "password": "supersecret1",
        "taste_profile": "savory, high protein",
    }
    first = client.post("/api/v1/users", json=payload)
    assert first.status_code == 201
    assert first.json()["taste_profile"] == "savory, high protein"
    assert first.json()["verified"] is False

    second = client.post("/api/v1/users", json=payload)
    assert second.status_code == 409


def test_bearer_sliding_and_logout() -> None:
    user_id, token = _register_verify_login("slide@example.com")
    auth = {"authorization": f"Bearer {token}"}

    before = MongoClient(os.environ["MONGODB_URI"])[os.environ["MONGODB_DB"]].sessions.find_one({})["expires_at"]
    r = client.get(f"/api/v1/users/{user_id}", headers=auth)
    assert r.status_code == 200
    after = MongoClient(os.environ["MONGODB_URI"])[os.environ["MONGODB_DB"]].sessions.find_one({})["expires_at"]
    assert after > before

    logout = client.post("/api/v1/auth/logout", headers=auth)
    assert logout.status_code == 204

    blocked = client.get(f"/api/v1/users/{user_id}", headers=auth)
    assert blocked.status_code == 401


def test_bootstrap_initial_recipes_once() -> None:
    user_id, token = _register_verify_login("boot@example.com")
    auth = {"authorization": f"Bearer {token}"}

    run1 = client.post(f"/api/v1/users/{user_id}/bootstrap-recipes", headers=auth)
    assert run1.status_code == 200
    assert run1.json()["count"] == 15
    assert run1.json()["categories"] == {"breakfast": 5, "lunch": 5, "dinner": 5}

    run2 = client.post(f"/api/v1/users/{user_id}/bootstrap-recipes", headers=auth)
    assert run2.status_code == 409


def test_recipe_crud_with_bearer() -> None:
    user_id, token = _register_verify_login("recipe@example.com")
    auth = {"authorization": f"Bearer {token}"}

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

    create = client.post("/api/v1/recipes", json=recipe, headers=auth)
    assert create.status_code == 201
    rid = create.json()["id"]

    list_r = client.get("/api/v1/recipes", headers=auth)
    assert list_r.status_code == 200
    assert len(list_r.json()) == 1

    patch = client.patch(f"/api/v1/recipes/{rid}", json={"minutes": 12}, headers=auth)
    assert patch.status_code == 200
    assert patch.json()["minutes"] == 12

    delete = client.delete(f"/api/v1/recipes/{rid}", headers=auth)
    assert delete.status_code == 204
