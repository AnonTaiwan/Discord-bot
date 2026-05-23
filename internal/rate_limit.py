from collections import defaultdict, deque
from time import monotonic
from typing import Hashable


class SlidingWindowRateLimiter:
    def __init__(self, limit: int = 3, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[Hashable, deque[float]] = defaultdict(deque)

    def allow(self, key: Hashable, limit: int | None = None, window_seconds: int | None = None) -> tuple[bool, float]:
        limit = self.limit if limit is None else limit
        window_seconds = self.window_seconds if window_seconds is None else window_seconds

        now = monotonic()
        events = self._events[key]
        cutoff = now - window_seconds

        while events and events[0] < cutoff:
            events.popleft()

        if len(events) >= limit:
            retry_after = window_seconds - (now - events[0])
            return False, max(0.0, retry_after)

        events.append(now)
        return True, 0.0
