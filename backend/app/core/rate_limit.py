import time
from collections import defaultdict
from typing import Callable, Dict, List
from fastapi import HTTPException, Request, status
from app.core.config import settings


class InMemoryRateLimiter:
    """
    Lightweight in-memory sliding window rate limiter.
    Documented per-process; suitable for single-instance / local host deployments.
    """

    def __init__(self):
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        if not settings.RATE_LIMIT_ENABLED:
            return True

        now = time.time()
        cutoff = now - window_seconds
        # Evict timestamps older than window
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

        if len(self._requests[key]) >= max_requests:
            return False

        self._requests[key].append(now)
        return True


rate_limiter = InMemoryRateLimiter()


def rate_limit(max_requests: int, window_seconds: int = 60) -> Callable:
    """FastAPI dependency for rate-limiting requests by client IP."""

    async def dependency(request: Request):
        if not settings.RATE_LIMIT_ENABLED or settings.ENVIRONMENT.lower() in ("test", "testing"):
            return

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        key = f"{client_ip}:{path}"

        if not rate_limiter.is_allowed(key, max_requests, window_seconds):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait before retrying.",
                headers={"Retry-After": str(window_seconds)},
            )

    return dependency
