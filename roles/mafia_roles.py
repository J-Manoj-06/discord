"""Mafia-aligned role implementations."""

from __future__ import annotations

from services.action_resolver import Action

from .base_role import MAFIA, PRIORITY, Role


class Godfather(Role):
    """Mafia leader that appears innocent to alignment checks."""

    action_type = "kill"

    def __init__(self):
        super().__init__("godfather", MAFIA, PRIORITY["kill"], unique=True)

    async def perform_action(self, game, player, target):
        return Action(player, target, "kill", self.priority, role_name=self.name)


class Mafia(Role):
    """Standard mafia member with a kill action."""

    action_type = "kill"

    def __init__(self):
        super().__init__("mafia", MAFIA, PRIORITY["kill"])

    async def perform_action(self, game, player, target):
        return Action(player, target, "kill", self.priority, role_name=self.name)


class Assassin(Role):
    """Limited independent kill charges."""

    action_type = "kill"

    def __init__(self):
        super().__init__("assassin", MAFIA, PRIORITY["kill"])

    async def perform_action(self, game, player, target):
        charges = game.setdefault("assassin_charges", {}).get(player, 1)
        if charges <= 0:
            return None
        game["assassin_charges"][player] = charges - 1
        return Action(player, target, "kill", self.priority, role_name=self.name)


class Framer(Role):
    """Frames targets to appear suspicious to investigations."""

    action_type = "redirect"

    def __init__(self):
        super().__init__("framer", MAFIA, PRIORITY["redirect"])

    async def perform_action(self, game, player, target):
        return Action(player, target, "redirect", self.priority, role_name=self.name)


class Disguiser(Role):
    """Hides own identity for one cycle by utility marker."""

    action_type = "utility"

    def __init__(self):
        super().__init__("disguiser", MAFIA, PRIORITY["utility"])

    async def perform_action(self, game, player, target):
        game.setdefault("disguised_players", set()).add(player)
        return Action(player, None, "utility", self.priority, role_name=self.name)


class Consigliere(Role):
    """Learns exact role name of a target."""

    action_type = "investigate"

    def __init__(self):
        super().__init__("consigliere", MAFIA, PRIORITY["investigate"])

    async def perform_action(self, game, player, target):
        return Action(player, target, "investigate_exact", self.priority, role_name=self.name)


class Poisoner(Role):
    """Applies delayed poison kill that resolves next night."""

    action_type = "delayed_kill"

    def __init__(self):
        super().__init__("poisoner", MAFIA, PRIORITY["delayed_kill"])

    async def perform_action(self, game, player, target):
        return Action(
            player,
            target,
            "delayed_kill_queue",
            self.priority,
            role_name=self.name,
            metadata={"nights_left": 1},
        )


class Silencer(Role):
    """Mutes one target for the upcoming day phase."""

    action_type = "utility"

    def __init__(self):
        super().__init__("silencer", MAFIA, PRIORITY["utility"])

    async def perform_action(self, game, player, target):
        return Action(player, target, "utility", self.priority, role_name=self.name)
