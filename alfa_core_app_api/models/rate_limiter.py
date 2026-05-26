# SPDX-License-Identifier: LGPL-3.0-only
"""In-memory token-bucket rate limiter for the AlfaCore API.

Pattern 10 — honest boundaries. This is in-memory per-worker state. For a
single Odoo worker in dev, that's correct. For multi-worker or multi-replica
production, this needs Redis-backed shared state — the algorithm stays the
same, only the storage backend swaps. The contract `RateLimiter.check()` is
the boundary between application code and storage so the swap is localized.

Algorithm: classic token bucket. Each key gets a bucket with a capacity
(burst size) and refill rate (tokens per second). Each request consumes
one token. If the bucket is empty, the request is rejected with a
retry-after hint.

Memory management: buckets are stored in an OrderedDict capped at
MAX_BUCKETS. When the cap is exceeded, the oldest bucket is evicted (LRU).
This bounds memory regardless of how many distinct keys hit the limiter.
"""

import threading
import time
from collections import OrderedDict

# Memory bound — evict oldest bucket when this many distinct keys are tracked.
# Sized for ~1000 active tokens + ~1000 unique source IPs.
MAX_BUCKETS = 5000


class TokenBucket:
    """A single bucket: capacity + refill rate."""

    __slots__ = ("capacity", "last_refill", "refill_rate", "tokens")

    def __init__(self, capacity: int, refill_rate_per_sec: float):
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate_per_sec)
        self.tokens = float(capacity)  # start full
        self.last_refill = time.monotonic()

    def consume(self, cost: float = 1.0):
        """Try to consume `cost` tokens. Returns (allowed: bool, retry_after_seconds: float)."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        if self.tokens >= cost:
            self.tokens -= cost
            return True, 0.0
        deficit = cost - self.tokens
        retry_after = deficit / self.refill_rate if self.refill_rate > 0 else float("inf")
        return False, retry_after


class RateLimiter:
    """Process-local limiter with named limit profiles.

    Profiles:
      auth      — credential-stuffing defense: 10 attempts/min, burst 5
      api_read  — per-token cap on read traffic: 120 req/min, burst 30
      api_ip    — secondary per-IP cap: 600 req/min, burst 100
                  (loose enough to allow legitimate multi-user behind NAT,
                  tight enough to slow scrapers)
    """

    PROFILES = {
        # capacity (burst), refill_rate_per_second
        "auth": (5, 10 / 60.0),
        "api_read": (30, 120 / 60.0),
        "api_ip": (100, 600 / 60.0),
    }

    def __init__(self):
        self._buckets = OrderedDict()  # key -> TokenBucket
        self._lock = threading.Lock()

    def check(self, profile: str, key: str, cost: float = 1.0):
        """Check whether a request should be allowed.

        Returns (allowed: bool, retry_after_seconds: float).
        retry_after is 0.0 when allowed; otherwise estimated seconds until
        the request would succeed.
        """
        if profile not in self.PROFILES:
            # Unknown profile — fail open. Don't break the API on misconfiguration.
            return True, 0.0
        capacity, refill_rate = self.PROFILES[profile]
        bucket_key = f"{profile}:{key}"

        with self._lock:
            bucket = self._buckets.get(bucket_key)
            if bucket is None:
                bucket = TokenBucket(capacity, refill_rate)
                self._buckets[bucket_key] = bucket
                # Evict oldest if over the memory cap
                if len(self._buckets) > MAX_BUCKETS:
                    self._buckets.popitem(last=False)
            else:
                # Move to MRU position
                self._buckets.move_to_end(bucket_key)

            return bucket.consume(cost)

    def reset(self, profile: str | None = None, key: str | None = None):
        """Reset state. Without args: clear everything. With profile+key:
        remove that single bucket. Used by tests and by an admin "unblock"
        action."""
        with self._lock:
            if profile is None and key is None:
                self._buckets.clear()
                return
            if profile and key:
                self._buckets.pop(f"{profile}:{key}", None)
                return
            # Profile-only or key-only: remove all matching
            to_remove = []
            for bk in self._buckets:
                bk_profile, _, bk_key = bk.partition(":")
                if profile and bk_profile != profile:
                    continue
                if key and bk_key != key:
                    continue
                to_remove.append(bk)
            for bk in to_remove:
                self._buckets.pop(bk)

    def stats(self):
        """Diagnostic: how many buckets are alive."""
        with self._lock:
            return {"total_buckets": len(self._buckets)}


# Module-level singleton. Per Odoo worker process.
limiter = RateLimiter()
