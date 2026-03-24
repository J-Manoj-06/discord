"""Core role abstractions and shared constants for the Mafia role engine."""

from __future__ import annotations

from typing import Any, Dict, Optional

VILLAGE = "village"
MAFIA = "mafia"
NEUTRAL = "neutral"
SPECIAL = "special"

PRIORITY = {
    "block": 1,
    "redirect": 2,
    "protect": 3,
    "kill": 4,
    "delayed_kill": 5,
    "investigate": 6,
    "utility": 7,
}


class Role:
    """Base role contract used by all concrete roles."""

    action_type: str = "utility"

    def __init__(self, name: str, team: str, priority: int, unique: bool = False):
        self.name = name
        self.team = team
        self.priority = priority
        self.unique = unique

    async def perform_action(self, game: Dict[str, Any], player: int, target: Optional[int]):
        """Build an action for the resolver.

        Concrete roles should return an Action instance, a list of Action instances,
        or None if no action should be queued.
        """
        raise NotImplementedError

    def can_use_action(self, action_type: str) -> bool:
        """Allow external handlers to validate whether a role can submit an action type."""
        return action_type == self.action_type

    def description(self) -> str:
        """Human-readable role summary used for DM notifications."""
        return f"You are the {self.name.title()}. Team: {self.team.title()}."
