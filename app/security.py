import base64
import hashlib
import hmac
import logging
import os
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.config import settings

logger = logging.getLogger(__name__)

RATE_BUCKET = defaultdict(deque)


def check_api_key(request: Request) -> None:
    key = request.headers.get("x-api-key")
    if key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def check_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 60
    bucket = RATE_BUCKET[ip]

    while bucket and (now - bucket[0]) > window:
        bucket.popleft()

    if len(bucket) >= settings.rate_limit_per_minute:
        logger.warning("rate_limit_exceeded ip=%s", ip)
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
