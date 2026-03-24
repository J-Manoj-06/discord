"""Game mode configuration service.

Stores per-guild mode config and provides mode validation, role pools,
minimum player requirements, and human-friendly mode descriptions.
"""

from __future__ import annotations

from typing import Dict, List


class ConfigService:
    """In-memory game config storage keyed by guild id."""

    # Requested mode role pools.
    MODE_ROLES = {
        "classic": [
            "godfather",
            "detective",
            "doctor",
            "villager",
        ],
        "advanced": [
            "godfather",
            "detective",
            "doctor",
            "villager",
            "baker",
            "baiter",
            "submissor",
            "sheriff",
            "bodyguard",
            "tracker",
        ],
        # "chaos" pulls from role registry at runtime in role manager.
        "chaos": "ALL",
    }

    MODE_MIN_PLAYERS = {
        "classic": 4,
        "advanced": 6,
        "chaos": 8,
    }

    MODE_DESCRIPTION = {
        "classic": "Beginner friendly",
        "advanced": "More roles added",
        "chaos": "All roles enabled",
    }

    def __init__(self):
        # game_config[guild_id] = {"mode": "classic"}
        self.game_config: Dict[int, Dict[str, str]] = {}

    def _get_or_create(self, guild_id: int) -> Dict[str, str]:
        if guild_id not in self.game_config:
            self.game_config[guild_id] = {"mode": "classic"}
        return self.game_config[guild_id]

    def is_valid_mode(self, mode: str) -> bool:
        return mode.lower().strip() in self.MODE_ROLES

    def set_mode(self, guild_id: int, mode: str) -> bool:
        normalized = mode.lower().strip()
        if not self.is_valid_mode(normalized):
            return False
        cfg = self._get_or_create(guild_id)
        cfg["mode"] = normalized
        return True

    def get_mode(self, guild_id: int) -> str:
        cfg = self._get_or_create(guild_id)
        return cfg.get("mode", "classic")

    def get_min_players(self, mode: str) -> int:
        return self.MODE_MIN_PLAYERS.get(mode.lower().strip(), 4)

    def get_mode_roles(self, mode: str) -> List[str] | str:
        return self.MODE_ROLES.get(mode.lower().strip(), self.MODE_ROLES["classic"])

    def get_mode_title(self, mode: str) -> str:
        normalized = mode.lower().strip()
        return normalized.capitalize()

    def get_mode_description(self, mode: str) -> str:
        normalized = mode.lower().strip()
        return self.MODE_DESCRIPTION.get(normalized, "Beginner friendly")
