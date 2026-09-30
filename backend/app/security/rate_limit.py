"""Rate limiting.

Two layers:
  * ``limiter``   – in-process sliding window (fast path, single worker).
  * ``db_limiter`` – PostgreSQL/aiosqlite counters so limits still hold when the
    API is scaled to several workers/instances (Render autoscaling).

Limits are always configurable by admins through ``competition_settings``.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.errors import RateLimited
from app.models.accounts import RateLimitCounter


@dataclass(slots=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after: int
    limit: int


class SlidingWindowLimiter:
    """Thread/async-safe in-memory limiter (monotonic clock, no wall-clock drift)."""

    MAX_KEYS = 20_000

    def __init__(self) -> None:
        self._buckets: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def hit(self, key: str, *, limit: int, window_seconds: int) -> RateLimitResult:
        if not settings.rate_limit_enabled or limit <= 0:
            return RateLimitResult(True, max(limit, 0), 0, limit)

        now = time.monotonic()
        cutoff = now - window_seconds
        async with self._lock:
            if len(self._buckets) > self.MAX_KEYS:  # pragma: no cover - memory guard
                self._prune(cutoff)
            bucket = self._buckets[key]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                retry_after = max(1, int(window_seconds - (now - bucket[0])) + 1)
                return RateLimitResult(False, 0, retry_after, limit)
            bucket.append(now)
            return RateLimitResult(True, max(0, limit - len(bucket)), 0, limit)

    async def peek(self, key: str, *, limit: int, window_seconds: int) -> RateLimitResult:
        now = time.monotonic()
        cutoff = now - window_seconds
        async with self._lock:
            bucket = self._buckets.get(key)
            if not bucket:
                return RateLimitResult(True, limit, 0, limit)
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            used = len(bucket)
            if used >= limit:
                return RateLimitResult(False, 0, max(1, int(window_seconds - (now - bucket[0])) + 1), limit)
            return RateLimitResult(True, limit - used, 0, limit)

    async def reset(self, key: str | None = None) -> None:
        async with self._lock:
            if key is None:
                self._buckets.clear()
            else:
                self._buckets.pop(key, None)

    def _prune(self, cutoff: float) -> None:
        stale = [k for k, v in self._buckets.items() if not v or v[-1] < cutoff]
        for key in stale:
            self._buckets.pop(key, None)


limiter = SlidingWindowLimiter()


async def enforce(
    key: str, *, limit: int, window_seconds: int = 60, message: str | None = None
) -> RateLimitResult:
    """Raise :class:`RateLimited` when the bucket is exhausted."""
    result = await limiter.hit(key, limit=limit, window_seconds=window_seconds)
    if not result.allowed:
        raise RateLimited(message, retry_after=result.retry_after)
    return result


async def enforce_persistent(
    session: AsyncSession,
    key: str,
    *,
    limit: int,
    window_seconds: int = 60,
    message: str | None = None,
) -> RateLimitResult:
    """DB-backed limiter for multi-worker deployments.

    Combines the in-process window with a durable counter row so horizontally
    scaled API instances share one budget per team/challenge.
    """
    local = await limiter.hit(key, limit=limit, window_seconds=window_seconds)
    if not local.allowed:
        raise RateLimited(message, retry_after=local.retry_after)

    if not settings.rate_limit_enabled or limit <= 0:
        return local

    now = datetime.now(UTC)
    row = await session.get(RateLimitCounter, key, with_for_update=True)
    if row is None:
        row = RateLimitCounter(key=key, window_start=now, count=1)
        session.add(row)
        try:
            await session.flush()
        except Exception:  # pragma: no cover - concurrent insert race
            await session.rollback()
            row = await session.get(RateLimitCounter, key, with_for_update=True)
            if row is None:
                return local
    if row is not None and (now - _aware(row.window_start)) >= timedelta(seconds=window_seconds):
        row.window_start = now
        row.count = 1
    elif row is not None:
        row.count += 1
    if row is not None and row.count > limit:
        retry_after = int(
            window_seconds - (now - _aware(row.window_start)).total_seconds()
        ) + 1
        raise RateLimited(message, retry_after=max(1, retry_after))
    await session.flush()
    return local


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


async def count_recent_rows(
    session: AsyncSession, model, *criteria, window_seconds: int, time_column_name: str = "submitted_at"
) -> int:
    """Count rows created inside a rolling window (used for anti-abuse stats)."""
    from sqlalchemy import func

    column = getattr(model, time_column_name)
    since = datetime.now(UTC) - timedelta(seconds=window_seconds)
    stmt = select(func.count()).select_from(model).where(column >= since, *criteria)
    return int((await session.execute(stmt)).scalar_one() or 0)
