"""Baker role implementation.

Neutral active role that gives bread with random effects.
Effect application and win-condition handling are managed by the resolver/game service.
"""

from __future__ import annotations

from services.action_resolver import Action

from .base_role import NEUTRAL, PRIORITY, Role


class Baker(Role):
    """Bread-giver neutral role with a target-based night action."""

    action_type = "utility"

    def __init__(self):
        # Run early so heal/distract can affect the same night.
        super().__init__("baker", NEUTRAL, PRIORITY["block"], unique=True)

    async def perform_action(self, game, player, target):
        return Action(player, target, "utility", self.priority, role_name=self.name)

    def description(self) -> str:
        return (
            "You are the Baker 🍞. Each night, give bread to one player. "
            "Bread applies a random effect. Win by giving bread to enough alive players "
            "while staying alive."
        )
