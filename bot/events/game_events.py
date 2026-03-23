"""
Game Events: Handlers for end-of-game rewards and progression updates.

This module should be called by your existing Mafia game logic
to award coins, XP, and update stats after each game.
"""
import logging

from services.economy_service import EconomyService
from services.profile_service import ProfileService

logger = logging.getLogger(__name__)


class GameEventsHandler:
    """Handle game-related events and reward distribution."""

    def __init__(self, economy_service: EconomyService, profile_service: ProfileService):
        self.economy = economy_service
        self.profile = profile_service

    async def on_game_ended(
        self,
        guild_id: int,
        winners: list,  # List of user IDs
        losers: list,  # List of user IDs
        role_map: dict,  # {user_id: role_name}
        votes_cast: dict,  # {user_id: vote_count}
    ):
        """
        Called when a Mafia game ends.

        Args:
            guild_id: Discord guild ID
            winners: List of winning player IDs
            losers: List of losing player IDs
            role_map: Dict mapping user ID to their role
            votes_cast: Dict mapping user ID to votes cast in voting phase
        """
        logger.info(
            f"Game ended in guild {guild_id}: "
            f"{len(winners)} winners, {len(losers)} losers"
        )

        # Process winners
        for user_id in winners:
            role = role_map.get(user_id, "villager")
            is_mafia = role == "mafia"
            votes = votes_cast.get(user_id, 0)

            # Award coins
            await self.economy.add_game_rewards(
                user_id,
                guild_id,
                is_winner=True,
                is_mafia=is_mafia,
                participated=True,
                votes_cast=votes,
            )

            # Add XP
            await self.profile.add_game_xp(
                user_id, guild_id, is_winner=True, participated=True
            )

            # Record stats
            await self.economy.record_game_stat(user_id, guild_id, is_winner=True)

            # Increment profile wins
            await self._increment_profile_wins(user_id, guild_id)

            logger.info(f"User {user_id} won game in guild {guild_id}")

        # Process losers
        for user_id in losers:
            role = role_map.get(user_id, "villager")
            votes = votes_cast.get(user_id, 0)

            # Award participation coins
            await self.economy.add_game_rewards(
                user_id,
                guild_id,
                is_winner=False,
                is_mafia=False,
                participated=True,
                votes_cast=votes,
            )

            # Add XP (less than winners)
            await self.profile.add_game_xp(
                user_id, guild_id, is_winner=False, participated=True
            )

            # Record stats
            await self.economy.record_game_stat(user_id, guild_id, is_winner=False)

            # Increment profile losses
            await self._increment_profile_losses(user_id, guild_id)

            logger.info(f"User {user_id} lost game in guild {guild_id}")

    async def on_player_voted(
        self, user_id: int, guild_id: int
    ):
        """Called when a player casts a vote in voting phase."""
        # Increment profile votes cast
        await self.profile.increment_votes_cast(user_id, guild_id)

    async def _increment_profile_wins(self, user_id: int, guild_id: int):
        """Increment user's win count in profile."""
        profile = await self.profile.get_profile(user_id, guild_id)
        await self.profile.profile_repo.update_wins(
            user_id, guild_id, profile.wins + 1
        )

    async def _increment_profile_losses(self, user_id: int, guild_id: int):
        """Increment user's loss count in profile."""
        profile = await self.profile.get_profile(user_id, guild_id)
        await self.profile.profile_repo.update_losses(
            user_id, guild_id, profile.losses + 1
        )


# Singleton instance (initialize this in your main bot file)
_game_events_handler: GameEventsHandler = None


def initialize_game_events(
    economy_service: EconomyService, profile_service: ProfileService
):
    """Initialize the game events handler."""
    global _game_events_handler
    _game_events_handler = GameEventsHandler(economy_service, profile_service)
    return _game_events_handler


def get_game_events_handler() -> GameEventsHandler:
    """Get the game events handler instance."""
    if _game_events_handler is None:
        raise RuntimeError("Game events handler not initialized!")
    return _game_events_handler
