"""Simple in-process rate limiting for authentication endpoints.

Without this, login is an unthrottled password oracle: an attacker can try
credentials as fast as the network allows.

Scope, stated plainly: counters live in this process's memory. With multiple
workers each holds its own, so the effective limit is roughly
`limit x worker_count`, and everything resets on restart. That is a meaningful
speed bump against credential stuffing, not a substitute for enforcement at the
edge. For production behind nginx or a load balancer, add a limit there too, or
back this with Redis.
"""
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request

# Trusted proxy headers are deliberately NOT consulted: any client can set
# X-Forwarded-For, so honouring it would let an attacker rotate their own key
# and bypass the limit entirely. Only the peer address is used.
TRUST_FORWARDED_HEADERS = False


class RateLimiter:
    """Fixed-window limiter keyed by client address.

    Used as a FastAPI dependency:

        @router.post("/login", dependencies=[Depends(login_limiter)])
    """

    def __init__(self, max_requests: int, window_seconds: int, name: str = "requests"):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.name = name
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = Lock()

    def _client_key(self, request: Request) -> str:
        if TRUST_FORWARDED_HEADERS:
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def check(self, key: str, now: float | None = None) -> tuple[bool, int]:
        """Record an attempt. Returns (allowed, seconds_until_retry)."""
        now = time.monotonic() if now is None else now
        cutoff = now - self.window_seconds

        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= cutoff:
                hits.popleft()

            if len(hits) >= self.max_requests:
                retry_after = max(1, int(hits[0] + self.window_seconds - now) + 1)
                return False, retry_after

            hits.append(now)

            # Opportunistic cleanup so idle keys don't accumulate forever.
            if len(self._hits) > 10_000:
                for k in [k for k, v in self._hits.items() if not v]:
                    del self._hits[k]

            return True, 0

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def __call__(self, request: Request) -> None:
        allowed, retry_after = self.check(self._client_key(request))
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Too many {self.name}. Please wait {retry_after} seconds "
                    f"and try again."
                ),
                headers={"Retry-After": str(retry_after)},
            )


# Login is the brute-force target, so it gets the tighter budget. Both are
# generous enough that a person who mistypes a password repeatedly is unaffected.
login_limiter = RateLimiter(max_requests=10, window_seconds=60, name="login attempts")
register_limiter = RateLimiter(max_requests=5, window_seconds=300, name="sign-up attempts")
