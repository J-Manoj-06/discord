"""Night action handler service for single-button role-driven action flow."""

from typing import Optional, Tuple

from services.role_engine import RoleEngine


class NightActionService:
    """Centralized API for role-based night action submission."""

    def __init__(self, game_service):
        self.game_service = game_service

    async def handle_night_action(
        self,
        guild_id: int,
        user_id: int,
        role: Optional[str],
        target_id: int,
    ) -> Tuple[bool, str]:
        """Validate and submit one role-appropriate night action."""
        session = self.game_service.get_session(guild_id)

        if session.get("phase") != "night":
            return False, "Night phase has ended."

        if user_id not in session.get("alive_players", []):
            return False, "Dead players cannot act."

        action_type = RoleEngine.get_action_type(role)
        if action_type is None:
            return False, "You have no night action."

        # Single-action safety: one submission per actor per night.
        marker_key = f"{user_id}:night_action"
        if marker_key in session.get("night_actions", {}):
            return False, "You already acted this night."

        ok, message = RoleEngine.validate_target(
            actor_id=user_id,
            target_id=target_id,
            role=role,
            alive_players=session.get("alive_players", []),
        )
        if not ok:
            return False, message

        if role == "baker" and target_id in session.get("bread_players", set()):
            return False, "That player already received bread."

        submit_ok, submit_message = await self.game_service.submit_night_action(
            guild_id=guild_id,
            actor_id=user_id,
            target_id=target_id,
            action_type=action_type,
        )
        if not submit_ok:
            return False, submit_message

        # Explicit once-per-night marker for the single-button flow.
        session.setdefault("night_actions", {})[marker_key] = target_id
        if role == "baker":
            return True, "Bread delivered 🍞"
        return True, "Action submitted."
