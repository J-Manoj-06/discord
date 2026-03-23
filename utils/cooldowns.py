"""
Cooldown utilities for managing command and action cooldowns.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Tuple


def utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def has_elapsed(last_ts: Optional[datetime], hours: int) -> bool:
    """Check if enough hours have elapsed since last_ts."""
    if last_ts is None:
        return True
    return utcnow() >= last_ts + timedelta(hours=hours)


def remaining_seconds(last_ts: Optional[datetime], hours: int) -> int:
    """Get remaining seconds until cooldown expires."""
    if last_ts is None:
        return 0
    delta = (last_ts + timedelta(hours=hours)) - utcnow()
    return max(0, int(delta.total_seconds()))


class CooldownManager:
    """Manage cooldowns for users and actions."""

    def __init__(self):
        self._cooldowns: Dict[Tuple[int, str], datetime] = {}

    def is_on_cooldown(
        self, user_id: int, action: str, hours: int = 1
    ) -> Tuple[bool, int]:
        """
        Check if user is on cooldown for an action.
        Returns (is_on_cooldown, remaining_seconds).
        """
        key = (user_id, action)
        last_use = self._cooldowns.get(key)

        if last_use is None:
            return False, 0

        remaining = remaining_seconds(last_use, hours)
        return remaining > 0, remaining

    def set_cooldown(self, user_id: int, action: str) -> None:
        """Set cooldown for a user action."""
        key = (user_id, action)
        self._cooldowns[key] = utcnow()

    def clear_cooldown(self, user_id: int, action: str) -> None:
        """Clear cooldown for a user action."""
        key = (user_id, action)
        if key in self._cooldowns:
            del self._cooldowns[key]
