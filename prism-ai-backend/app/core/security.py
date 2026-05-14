from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import Settings


@dataclass
class RateLimitBucket:
    requests: deque[float]


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings
        self._buckets: dict[str, RateLimitBucket] = defaultdict(lambda: RateLimitBucket(deque()))

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        if self.settings.rate_limit_per_minute <= 0:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60
        bucket = self._buckets[client_ip]
        while bucket.requests and bucket.requests[0] < window_start:
            bucket.requests.popleft()

        if len(bucket.requests) >= self.settings.rate_limit_per_minute:
            return Response(content='{"detail":"rate limit exceeded"}', status_code=429, media_type="application/json")

        bucket.requests.append(now)
        return await call_next(request)
