"""Tests for auth rate limiting.

The window logic is tested directly with an injected clock so the suite doesn't
sleep, plus an end-to-end check that login actually starts returning 429.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from app.services.rate_limit import TRUST_FORWARDED_HEADERS, RateLimiter


class TestWindow:
    def test_allows_up_to_the_limit(self):
        rl = RateLimiter(max_requests=3, window_seconds=60)
        assert [rl.check("ip", now=0)[0] for _ in range(3)] == [True, True, True]

    def test_blocks_beyond_the_limit(self):
        rl = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            rl.check("ip", now=0)
        allowed, retry_after = rl.check("ip", now=0)
        assert allowed is False
        assert retry_after > 0

    def test_window_expires(self):
        rl = RateLimiter(max_requests=2, window_seconds=60)
        rl.check("ip", now=0)
        rl.check("ip", now=0)
        assert rl.check("ip", now=30)[0] is False      # still inside the window
        assert rl.check("ip", now=61)[0] is True       # window has rolled over

    def test_clients_are_tracked_separately(self):
        """One client exhausting its budget must not lock out everyone else."""
        rl = RateLimiter(max_requests=2, window_seconds=60)
        rl.check("attacker", now=0)
        rl.check("attacker", now=0)
        assert rl.check("attacker", now=0)[0] is False
        assert rl.check("innocent", now=0)[0] is True

    def test_retry_after_shrinks_as_the_window_advances(self):
        rl = RateLimiter(max_requests=1, window_seconds=60)
        rl.check("ip", now=0)
        _, early = rl.check("ip", now=1)
        _, late = rl.check("ip", now=50)
        assert late < early

    def test_reset_clears_state(self):
        rl = RateLimiter(max_requests=1, window_seconds=60)
        rl.check("ip", now=0)
        assert rl.check("ip", now=0)[0] is False
        rl.reset()
        assert rl.check("ip", now=0)[0] is True


class TestSpoofingResistance:
    def test_forwarded_headers_are_not_trusted(self):
        """Honouring X-Forwarded-For would let a client rotate its own key."""
        assert TRUST_FORWARDED_HEADERS is False


@pytest.mark.integration
class TestLoginEndpoint:
    def test_repeated_failures_eventually_return_429(self, client):
        from app.services.rate_limit import login_limiter
        login_limiter.reset()

        client.post("/api/auth/register", json={
            "full_name": "Ada", "email": "ada@example.com", "password": "secret123",
        })

        statuses = [
            client.post("/api/auth/login", data={
                "username": "ada@example.com", "password": "wrong",
            }).status_code
            for _ in range(15)
        ]
        assert 401 in statuses, "expected some attempts to be rejected normally"
        assert 429 in statuses, "brute force was never throttled"

        blocked = client.post("/api/auth/login", data={
            "username": "ada@example.com", "password": "wrong",
        })
        assert blocked.status_code == 429
        assert "Retry-After" in blocked.headers
        login_limiter.reset()

    def test_correct_password_still_works_below_the_limit(self, client):
        from app.services.rate_limit import login_limiter
        login_limiter.reset()
        client.post("/api/auth/register", json={
            "full_name": "Ada", "email": "ada@example.com", "password": "secret123",
        })
        r = client.post("/api/auth/login", data={
            "username": "ada@example.com", "password": "secret123",
        })
        assert r.status_code == 200
        login_limiter.reset()
