import base64
import hashlib
import hmac
import os
import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from fastapi import HTTPException, Request, status

from app.config import settings
from app.db_mongo import get_db

RATE_BUCKET = defaultdict(deque)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def check_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 60
    bucket = RATE_BUCKET[ip]

    while bucket and (now - bucket[0]) > window:
        bucket.popleft()

    if len(bucket) >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    bucket.append(now)


def hash_email(email: str) -> str:
    normalized = email.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=64,
    )
    return f"scrypt${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algo, salt_b64, digest_b64 = password_hash.split("$", 2)
        if algo != "scrypt":
            return False
        salt = base64.b64decode(salt_b64.encode())
        expected = base64.b64decode(digest_b64.encode())
        check = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=2**14,
            r=8,
            p=1,
            dklen=64,
        )
        return hmac.compare_digest(check, expected)
    except Exception:
        return False


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def issue_bearer_token(user_id: str) -> tuple[str, int]:
    ttl_seconds = settings.token_ttl_hours * 3600
    raw = secrets.token_urlsafe(48)
    expires_at = _utc_now() + timedelta(seconds=ttl_seconds)

    get_db().sessions.insert_one(
        {
            "token_hash": hash_token(raw),
            "user_id": user_id,
            "revoked": False,
            "created_at": _utc_now().isoformat(),
            "last_used_at": _utc_now().isoformat(),
            "expires_at": expires_at.isoformat(),
        }
    )
    return raw, ttl_seconds


def _extract_bearer(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return auth.split(" ", 1)[1].strip()


def get_current_user(request: Request) -> dict:
    check_rate_limit(request)
    raw = _extract_bearer(request)
    token_hash = hash_token(raw)

    session = get_db().sessions.find_one({"token_hash": token_hash, "revoked": False})
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if _parse_iso(session["expires_at"]) <= _utc_now():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

    # sliding expiration
    new_exp = _utc_now() + timedelta(hours=settings.token_ttl_hours)
    get_db().sessions.update_one(
        {"_id": session["_id"]},
        {"$set": {"last_used_at": _utc_now().isoformat(), "expires_at": new_exp.isoformat()}},
    )

    user = get_db().users.find_one({"_id": ObjectId(session["user_id"]), "is_active": True})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not active")

    return user


def revoke_current_token(request: Request) -> None:
    raw = _extract_bearer(request)
    get_db().sessions.update_one({"token_hash": hash_token(raw)}, {"$set": {"revoked": True}})
