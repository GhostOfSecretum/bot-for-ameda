from __future__ import annotations

from datetime import datetime, timedelta, timezone


MOSCOW_TZ = timezone(timedelta(hours=3), name="Europe/Moscow")


def now_moscow() -> datetime:
    return datetime.now(MOSCOW_TZ)


def now_iso(*, timespec: str = "seconds") -> str:
    # Keep naive ISO output format used across the project, but in Moscow time.
    return now_moscow().replace(tzinfo=None).isoformat(timespec=timespec)


def now_compact_timestamp() -> str:
    return now_moscow().strftime("%Y%m%d_%H%M%S_%f")
