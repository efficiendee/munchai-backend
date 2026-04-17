from __future__ import annotations

from datetime import datetime, timezone

from pymongo import ASCENDING, MongoClient
from pymongo.database import Database

from app.config import settings

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
    return _client


def get_db() -> Database:
    return get_client()[settings.mongodb_db]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_indexes() -> None:
    db = get_db()
    db.users.create_index([("email_hash", ASCENDING)], unique=True, name="uniq_email_hash")
    db.users.create_index([("username", ASCENDING)], unique=False, name="idx_username")
    db.recipes.create_index([("title", ASCENDING)], unique=False, name="idx_recipe_title")


def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
