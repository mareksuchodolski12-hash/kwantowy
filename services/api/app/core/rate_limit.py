"""Simple token-bucket rate limiter backed by Redis.

Uses the existing Redis connection infrastructure.  Falls open (allows the
request) if Redis is unavailable so a Redis hiccup doesn't take down the API.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import Request
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.config import settings

# Requests per window per source IP.
_DEFAULT_LIMIT = 120
_WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP sliding-window rate limiter.

    Skips health/metrics endpoints to avoid interfering with probes.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # Don't rate-limit infrastructure endpoints.
        if request.url.path in ("/healthz", "/readyz", "/metrics"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"qcp:ratelimit:{client_ip}"

        try:
            redis = Redis.from_url(settings.redis_url, socket_connect_timeout=1)
            try:
                current = await redis.incr(key)
                if current == 1:
                    await redis.expire(key, _WINDOW_SECONDS)
                if current > _DEFAULT_LIMIT:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded. Try again later."},
                        headers={"Retry-After": str(_WINDOW_SECONDS)},
                    )
            finally:
                await redis.close()
        except Exception:
            # Fail open — allow the request if Redis is unreachable.
            pass

        return await call_next(request)
