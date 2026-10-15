"""A tiny in-process sliding-window rate limiter.

Good enough for a personal site on one worker. If you ever run multiple
uvicorn workers, either pin ``--workers 1`` or move this to Redis.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(
        self,
        limit: int,
        window_seconds: int,
        *,
        max_keys: int = 20_000,
        clock=time.monotonic,
    ) -> None:
        self.limit = max(int(limit), 1)
        self.window = max(int(window_seconds), 1)
        self.max_keys = max(int(max_keys), 1)
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> tuple[bool, int]:
        """Register one attempt.

        Returns ``(allowed, retry_after_seconds)``; ``retry_after`` is 0 when the
        attempt is allowed.
        """

        now = self._clock()
        with self._lock:
            if len(self._hits) > self.max_keys:
                self._evict(now)

            bucket = self._hits[key]
            while bucket and now - bucket[0] >= self.window:
                bucket.popleft()

            if len(bucket) >= self.limit:
                retry_after = max(int(self.window - (now - bucket[0])) + 1, 1)
                return False, retry_after

            bucket.append(now)
            return True, 0

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def _evict(self, now: float) -> None:
        stale = [key for key, bucket in self._hits.items() if not bucket or now - bucket[-1] >= self.window]
        for key in stale:
            del self._hits[key]
        if len(self._hits) > self.max_keys:
            self._hits.clear()
