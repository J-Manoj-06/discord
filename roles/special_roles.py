"""Special chaos-oriented role implementations."""

from __future__ import annotations

import random

from services.action_resolver import Action

from .base_role import PRIORITY, SPECIAL, Role


class TimeTraveler(Role):
    """Can undo the latest death one time per game."""

    action_type = "utility"

    def __init__(self):
        super().__init__("timetraveler", SPECIAL, PRIORITY["utility"], unique=True)

    async def perform_action(self, game, player, target):
        if game.get("time_travel_used", False):
            return None
        return Action(player, None, "utility", self.priority, role_name=self.name)


class Gambler(Role):
    """Randomly chooses a kill, protect, or investigate effect."""

    action_type = "utility"

    def __init__(self):
        super().__init__("gambler", SPECIAL, PRIORITY["utility"])

    async def perform_action(self, game, player, target):
        roll = random.choice(["kill", "protect", "investigate"])
        return Action(player, target, roll, PRIORITY[roll], role_name=self.name)


class Shapeshifter(Role):
    """Copies another role's action profile for one night."""

    action_type = "utility"

    def __init__(self):
        super().__init__("shapeshifter", SPECIAL, PRIORITY["utility"])

    async def perform_action(self, game, player, target):
        copied_role = game.get("shapeshift_targets", {}).get(player)
        if copied_role:
            game.setdefault("copied_roles", {})[player] = copied_role
        return Action(player, target, "utility", self.priority, role_name=self.name)


class Magnet(Role):
    """Forces vote gravity toward a selected target."""

    action_type = "redirect"

    def __init__(self):
        super().__init__("magnet", SPECIAL, PRIORITY["redirect"])

    async def perform_action(self, game, player, target):
        return Action(
            player,
            target,
            "utility",
            PRIORITY["utility"],
            role_name=self.name,
            metadata={"forced_target": target},
        )


class Trickster(Role):
    """Randomizes queued targets by setting redirect map."""

    action_type = "redirect"

    def __init__(self):
        super().__init__("trickster", SPECIAL, PRIORITY["redirect"])

    async def perform_action(self, game, player, target):
        alive = [pid for pid in game.get("alive_players", []) if pid != player]
        if alive:
            mapping = {}
            for pid in alive:
                mapping[pid] = random.choice(alive)
            game["trickster_redirect"] = mapping
        return Action(player, target, "redirect", self.priority, role_name=self.name)
