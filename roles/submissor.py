"""Submissor role implementation.

Neutral role with no active night ability.
Conversion/inheritance behavior is handled by the night resolver and game service.
"""

from __future__ import annotations

from .base_role import NEUTRAL, PRIORITY, Role


class Submissor(Role):
    """No active ability. Converts on first attack, dies on second."""

    action_type = "none"

    def __init__(self):
        super().__init__("submissor", NEUTRAL, PRIORITY["utility"], unique=True)

    async def perform_action(self, game, player, target):
        return None

    def description(self) -> str:
        return (
            "You are the Submissor. You have no active night ability. "
            "First attack converts you to the attacker's side; second attack kills you."
        )
