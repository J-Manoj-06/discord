"""Neutral role implementations."""

from __future__ import annotations

from services.action_resolver import Action

from .base_role import NEUTRAL, PRIORITY, Role

NEUTRAL_ROLE_NAMES = {
    "jester",
    "serialkiller",
    "executioner",
    "arsonist",
    "vampire",
    "submissor",
}


class Jester(Role):
    """Wins by being voted out; no standard night action."""

    action_type = "utility"

    def __init__(self):
        super().__init__("jester", NEUTRAL, PRIORITY["utility"], unique=True)

    async def perform_action(self, game, player, target):
        return Action(player, None, "utility", self.priority, role_name=self.name)


class SerialKiller(Role):
    """Independent killer that attacks nightly."""

    action_type = "kill"

    def __init__(self):
        super().__init__("serialkiller", NEUTRAL, PRIORITY["kill"], unique=True)

    async def perform_action(self, game, player, target):
        return Action(player, target, "kill", self.priority, role_name=self.name)


class Executioner(Role):
    """Wins if their assigned target is eliminated."""

    action_type = "utility"

    def __init__(self):
        super().__init__("executioner", NEUTRAL, PRIORITY["utility"], unique=True)

    async def perform_action(self, game, player, target):
        if target is not None:
            game.setdefault("executioner_targets", {})[player] = target
        return Action(player, target, "utility", self.priority, role_name=self.name)


class Arsonist(Role):
    """Douses targets and can ignite all previously doused players."""

    action_type = "utility"

    def __init__(self):
        super().__init__("arsonist", NEUTRAL, PRIORITY["utility"], unique=True)

    async def perform_action(self, game, player, target):
        ignite = bool(game.get("arsonist_ignite", {}).get(player))
        if ignite:
            doused = game.get("doused_targets", {}).get(player, set())
            actions = [
                Action(player, victim, "kill", PRIORITY["kill"], role_name=self.name)
                for victim in doused
            ]
            game.setdefault("doused_targets", {})[player] = set()
            return actions

        if target is not None:
            game.setdefault("doused_targets", {}).setdefault(player, set()).add(target)
        return Action(player, target, "utility", self.priority, role_name=self.name)


class Vampire(Role):
    """Attempts to convert a target into vampire alignment."""

    action_type = "utility"

    def __init__(self):
        super().__init__("vampire", NEUTRAL, PRIORITY["utility"], unique=True)

    async def perform_action(self, game, player, target):
        if target is not None:
            game.setdefault("pending_conversions", []).append({"source": player, "target": target})
        return Action(player, target, "utility", self.priority, role_name=self.name)
