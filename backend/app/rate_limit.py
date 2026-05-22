"""Simple in-memory rate limiting per client IP."""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, Request

from app.config import get_settings

_buckets: dict[str, list[float]] = defaultdict(list)


async def rate_limit_middleware(request: Request, call_next):
    if request.url.path in ("/health", "/api/cloud/status"):
        return await call_next(request)

    settings = get_settings()
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 60.0
    key = ip
    _buckets[key] = [t for t in _buckets[key] if now - t < window]

    if len(_buckets[key]) >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again shortly.")

    _buckets[key].append(now)
    return await call_next(request)
