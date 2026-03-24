"""Village-aligned role implementations."""

from __future__ import annotations

from services.action_resolver import Action

from .base_role import PRIORITY, VILLAGE, Role


class Villager(Role):
    """Vanilla village role with no night power."""

    action_type = "utility"

    def __init__(self):
        super().__init__("villager", VILLAGE, PRIORITY["utility"])

    async def perform_action(self, game, player, target):
        return None


class Detective(Role):
    """Investigates alignment at night."""

    action_type = "investigate"

    def __init__(self):
        super().__init__("detective", VILLAGE, PRIORITY["investigate"], unique=True)

    async def perform_action(self, game, player, target):
        return Action(player, target, "investigate", self.priority, role_name=self.name)


class Doctor(Role):
    """Protects one player from lethal actions."""

    action_type = "protect"

    def __init__(self):
        super().__init__("doctor", VILLAGE, PRIORITY["protect"])

    async def perform_action(self, game, player, target):
        return Action(player, target, "protect", self.priority, role_name=self.name)


class Bodyguard(Role):
    """Intercepts kills and dies in place of protected target."""

    action_type = "protect"

    def __init__(self):
        super().__init__("bodyguard", VILLAGE, PRIORITY["protect"])

    async def perform_action(self, game, player, target):
        return Action(player, target, "protect", self.priority, role_name=self.name)


class Sheriff(Role):
    """Investigates whether a target looks suspicious."""

    action_type = "investigate"

    def __init__(self):
        super().__init__("sheriff", VILLAGE, PRIORITY["investigate"])

    async def perform_action(self, game, player, target):
        return Action(player, target, "investigate", self.priority, role_name=self.name)


class Mayor(Role):
    """Grants double voting strength during the day."""

    action_type = "utility"

    def __init__(self):
        super().__init__("mayor", VILLAGE, PRIORITY["utility"], unique=True)

    async def perform_action(self, game, player, target):
        game.setdefault("double_voters", set()).add(player)
        return Action(player, None, "utility", self.priority, role_name=self.name)


class Tracker(Role):
    """Tracks who a target visits at night."""

    action_type = "investigate"

    def __init__(self):
        super().__init__("tracker", VILLAGE, PRIORITY["investigate"])

    async def perform_action(self, game, player, target):
        return Action(
            player,
            target,
            "investigate",
            self.priority,
            role_name=self.name,
            metadata={"mode": "track"},
        )


class Lookout(Role):
    """Watches visitors to a chosen target."""

    action_type = "investigate"

    def __init__(self):
        super().__init__("lookout", VILLAGE, PRIORITY["investigate"])

    async def perform_action(self, game, player, target):
        return Action(
            player,
            target,
            "investigate",
            self.priority,
            role_name=self.name,
            metadata={"mode": "lookout"},
        )


class GuardianAngel(Role):
    """Protects a fixed assigned player each night."""

    action_type = "protect"

    def __init__(self):
        super().__init__("guardianangel", VILLAGE, PRIORITY["protect"])

    async def perform_action(self, game, player, target):
        fixed = game.get("guardian_targets", {}).get(player)
        return Action(
            player,
            fixed,
            "protect",
            self.priority,
            role_name=self.name,
            metadata={"fixed_target": fixed},
        )


class Spy(Role):
    """Collects intel on mafia actions each night."""

    action_type = "investigate"

    def __init__(self):
        super().__init__("spy", VILLAGE, PRIORITY["investigate"])

    async def perform_action(self, game, player, target):
        return Action(
            player,
            target,
            "investigate",
            self.priority,
            role_name=self.name,
            metadata={"mode": "spy"},
        )


class Medium(Role):
    """Can communicate with dead players by utility effect."""

    action_type = "utility"

    def __init__(self):
        super().__init__("medium", VILLAGE, PRIORITY["utility"])

    async def perform_action(self, game, player, target):
        game.setdefault("dead_chat_enabled", set()).add(player)
        return Action(player, None, "utility", self.priority, role_name=self.name)
