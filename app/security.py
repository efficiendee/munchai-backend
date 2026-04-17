import logging
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.config import settings

logger = logging.getLogger(__name__)

RATE_BUCKET = defaultdict(deque)


def check_api_key(request: Request) -> None:
    key = request.headers.get("x-api-key")
    if key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


def check_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 60
    bucket = RATE_BUCKET[ip]

    while bucket and (now - bucket[0]) > window:
        bucket.popleft()

    if len(bucket) >= settings.rate_limit_per_minute:
        logger.warning("rate_limit_exceeded ip=%s", ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )

    bucket.append(now)
