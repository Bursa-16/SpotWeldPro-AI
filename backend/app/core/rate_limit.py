"""Per-process sliding-window rate limiter for public endpoints.

WARNING — DEPLOYMENT SCOPE:
  This is an in-process, in-memory rate limiter. In a multi-worker deployment
  (multiple uvicorn workers, gunicorn processes, Kubernetes pods) each worker
  maintains its own independent bucket state. The effective global rate is
  N_workers × limit_per_window.

  This limiter is appropriate for:
    - Single-worker development and staging servers.
    - A first line of defence against trivial abuse by individual callers.

  For production multi-worker deployments that require a global rate guarantee,
  replace _PUBLIC_DEMO_LIMITER with a Redis-backed implementation and keep
  this module as a fallback.

IP RESOLUTION POLICY:
  The limiter uses request.client.host (the direct TCP peer address) as the
  rate-limit key. X-Forwarded-For and X-Real-IP headers are intentionally
  NOT trusted: without an explicit trusted-proxy allowlist, those headers can
  be forged by the client to bypass per-IP limits.

  If the application is deployed behind a trusted reverse proxy, update
  get_client_ip() to read the forwarded header only after verifying the
  request arrived from a known proxy address.

MEMORY SAFETY:
  _MAX_TRACKED_IPS caps the number of distinct IP buckets held in memory.
  When the cap is reached the oldest bucket (fewest recent requests) is evicted.
  All timestamps older than the window are purged on every check, so the
  working memory per tracked IP is bounded by (limit × 8 bytes for floats).
"""
from __future__ import annotations

from collections import deque
from threading import Lock
from time import monotonic
from typing import Optional

from fastapi import Request

# Public demo rate: 60 requests / IP / 60 seconds.
# Rationale: the endpoint performs bounded in-memory CPU computation (no DB).
# 60 req/min (1/sec average) allows interactive testing while preventing
# trivial flood attacks from a single unauthenticated caller.
_PUBLIC_DEMO_LIMIT: int = 60
_PUBLIC_DEMO_WINDOW_SECONDS: int = 60

# Memory cap: at most this many distinct IPs tracked at once.
# At limit × 8 bytes/bucket that is ≤ ~480 KB total.
_MAX_TRACKED_IPS: int = 10_000


class SlidingWindowRateLimiter:
    """Thread-safe sliding-window counter keyed by arbitrary string (typically IP)."""

    def __init__(self, limit: int, window_seconds: int) -> None:
        self._limit = limit
        self._window = window_seconds
        self._buckets: dict[str, deque[float]] = {}
        self._lock = Lock()

    @property
    def limit(self) -> int:
        return self._limit

    @property
    def window_seconds(self) -> int:
        return self._window

    def is_allowed(self, key: str) -> tuple[bool, int]:
        """Return (allowed, remaining_after_this_request).

        Thread-safe. Evicts stale timestamps and enforces the window.
        """
        now = monotonic()
        cutoff = now - self._window
        with self._lock:
            if key not in self._buckets:
                if len(self._buckets) >= _MAX_TRACKED_IPS:
                    self._evict_oldest()
                self._buckets[key] = deque()
            bucket = self._buckets[key]
            # Purge expired timestamps.
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self._limit:
                return False, 0
            bucket.append(now)
            return True, self._limit - len(bucket)

    def reset_key(self, key: str) -> None:
        """Remove all recorded timestamps for key. Used in tests only."""
        with self._lock:
            self._buckets.pop(key, None)

    def _evict_oldest(self) -> None:
        """Remove the bucket whose most-recent timestamp is farthest in the past."""
        oldest_key = min(
            self._buckets,
            key=lambda k: self._buckets[k][-1] if self._buckets[k] else 0.0,
        )
        del self._buckets[oldest_key]


# Module-level singleton for the public demo endpoint.
# Tests may call PUBLIC_DEMO_LIMITER.reset_key(key) to clear a bucket.
PUBLIC_DEMO_LIMITER = SlidingWindowRateLimiter(
    limit=_PUBLIC_DEMO_LIMIT,
    window_seconds=_PUBLIC_DEMO_WINDOW_SECONDS,
)


def get_client_ip(request: Request) -> str:
    """Extract the rate-limit key (direct peer IP) from the request.

    Does NOT trust X-Forwarded-For without trusted-proxy verification.
    Falls back to "unknown" if client information is unavailable
    (e.g. some test transports).
    """
    if request.client and request.client.host:
        return request.client.host
    return "unknown"
