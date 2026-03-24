"""Role Engine: central role-night-action mapping and target rules."""

from typing import Optional, Tuple


class RoleEngine:
    """Centralized role action rules used by night action handlers."""

    ROLE_TEAM = {
        "godfather": "mafia",
        "doctor": "town",
        "detective": "town",
        "villager": "town",
        "submissor": "neutral",
    }

    ACTION_MAP = {
        "godfather": "kill",
        "doctor": "heal",
        "detective": "investigate",
    }

    @classmethod
    def get_action_type(cls, role: Optional[str]) -> Optional[str]:
        """Return UI action type for a role or None if role has no night action."""
        if not role:
            return None
        return cls.ACTION_MAP.get(role.lower())

    @classmethod
    def get_role_team(cls, role: Optional[str]) -> str:
        """Return baseline team label for a role name."""
        if not role:
            return "neutral"
        return cls.ROLE_TEAM.get(role.lower(), "neutral")

    @classmethod
    def has_night_action(cls, role: Optional[str]) -> bool:
        """Whether the role has a selectable night action."""
        return cls.get_action_type(role) is not None

    @staticmethod
    def can_target_self(role: Optional[str]) -> bool:
        """Doctor can self-protect. Others in this simplified flow cannot self-target."""
        return (role or "").lower() == "doctor"

    @classmethod
    def validate_target(
        cls,
        actor_id: int,
        target_id: int,
        role: Optional[str],
        alive_players: list[int],
    ) -> Tuple[bool, str]:
        """Validate target against role rules and alive-state constraints."""
        if actor_id not in alive_players:
            return False, "Dead players cannot act."

        if target_id not in alive_players:
            return False, "Target is not alive."

        if actor_id == target_id and not cls.can_target_self(role):
            return False, "You cannot target yourself for this role."

        return True, "ok"
