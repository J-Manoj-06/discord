"""Baiter role implementation.

Minimal implementation so Advanced mode role pool can include `baiter` safely.
"""

from __future__ import annotations

from .base_role import PRIORITY, VILLAGE, Role


class Baiter(Role):
    """Village-aligned utility role with no active night action in current ruleset."""

    action_type = "none"

    def __init__(self):
        super().__init__("baiter", VILLAGE, PRIORITY["utility"], unique=True)

    async def perform_action(self, game, player, target):
        return None
