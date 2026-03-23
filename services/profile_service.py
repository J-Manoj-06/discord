"""
Profile Service: Handles user levels, XP, stats, and cosmetic selections.
Manages progression and profile data consistency.
"""
import logging
from typing import Optional, Tuple

from database.repositories.profile_repository import ProfileRepository
from models.user_profile import UserProfile

logger = logging.getLogger(__name__)

# XP required per level (can be tuned)
XP_PER_LEVEL = 100


class ProfileService:
    """Service for managing user profiles, levels, and cosmetics."""

    def __init__(self, profile_repo: ProfileRepository):
        self.profile_repo = profile_repo

    async def get_profile(self, user_id: int, guild_id: int) -> UserProfile:
        """Get or create a user's profile."""
        profile = await self.profile_repo.find_by_user_guild(user_id, guild_id)
        if not profile:
            profile = await self.profile_repo.create(user_id, guild_id)
            logger.info(f"Created profile for user {user_id} in guild {guild_id}")
        return profile

    async def add_xp(
        self, user_id: int, guild_id: int, amount: int
    ) -> Tuple[bool, Optional[int]]:
        """
        Add XP and handle level-ups.
        Returns (success, new_level_if_leveled_up_else_None).
        """
        profile = await self.get_profile(user_id, guild_id)
        new_xp = profile.xp + amount

        # Calculate if level up
        current_level = profile.level
        new_level = 1 + (new_xp // XP_PER_LEVEL)

        leveled_up = new_level > current_level

        updated = await self.profile_repo.update_xp_and_level(
            user_id, guild_id, new_xp, new_level if leveled_up else current_level
        )

        if updated:
            logger.info(f"User {user_id} earned {amount} XP")
            if leveled_up:
                logger.info(f"User {user_id} leveled up to {new_level}")
                return True, new_level
            return True, None

        return False, None

    def get_xp_for_next_level(self, current_level: int) -> int:
        """Get total XP needed to reach next level."""
        return (current_level + 1) * XP_PER_LEVEL

    def get_xp_progress(self, xp: int, level: int) -> Tuple[int, int]:
        """
        Get current XP in level and total XP for that level.
        Returns (current_xp_in_level, total_xp_needed_for_level).
        """
        level_start_xp = level * XP_PER_LEVEL
        level_end_xp = (level + 1) * XP_PER_LEVEL
        current_xp_in_level = xp - level_start_xp
        xp_for_level = level_end_xp - level_start_xp
        return current_xp_in_level, xp_for_level

    async def add_game_xp(
        self, user_id: int, guild_id: int, is_winner: bool, participated: bool
    ) -> Tuple[bool, Optional[int]]:
        """
        Award XP based on game outcome.
        Returns (success, new_level_if_leveled_else_None).
        """
        if not participated:
            return True, None

        xp_earned = 50 if is_winner else 25
        return await self.add_xp(user_id, guild_id, xp_earned)

    async def set_equipped_title(
        self, user_id: int, guild_id: int, title: str
    ) -> bool:
        """Set user's equipped title."""
        return await self.profile_repo.update_equipped_title(user_id, guild_id, title)

    async def set_equipped_theme(
        self, user_id: int, guild_id: int, theme: str
    ) -> bool:
        """Set user's equipped profile theme."""
        return await self.profile_repo.update_equipped_theme(user_id, guild_id, theme)

    async def get_win_rate(self, user_id: int, guild_id: int) -> float:
        """Calculate user's win rate as percentage."""
        profile = await self.get_profile(user_id, guild_id)
        if profile.games_played == 0:
            return 0.0
        return (profile.wins / profile.games_played) * 100

    async def set_display_name(
        self, user_id: int, guild_id: int, name: str
    ) -> bool:
        """Set user's display name. Max 32 chars."""
        if len(name) > 32:
            return False
        return await self.profile_repo.update_display_name(user_id, guild_id, name)

    async def set_favorite_role(
        self, user_id: int, guild_id: int, role: str
    ) -> bool:
        """Set user's favorite Mafia role."""
        valid_roles = ["mafia", "detective", "doctor", "villager"]
        if role.lower() not in valid_roles:
            return False
        return await self.profile_repo.update_favorite_role(
            user_id, guild_id, role.lower()
        )

    async def increment_votes_cast(self, user_id: int, guild_id: int) -> bool:
        """Increment votes cast counter."""
        profile = await self.get_profile(user_id, guild_id)
        return await self.profile_repo.update_votes_cast(
            user_id, guild_id, profile.votes_cast + 1
        )

    async def add_unlocked_cosmetic(
        self, user_id: int, guild_id: int, cosmetic_id: str
    ) -> bool:
        """Add cosmetic to user's unlocked list."""
        profile = await self.get_profile(user_id, guild_id)
        if cosmetic_id not in profile.unlocked_cosmetics:
            profile.unlocked_cosmetics.append(cosmetic_id)
            return await self.profile_repo.update_unlocked_cosmetics(
                user_id, guild_id, profile.unlocked_cosmetics
            )
        return True

    async def has_cosmetic(
        self, user_id: int, guild_id: int, cosmetic_id: str
    ) -> bool:
        """Check if user has unlocked a cosmetic."""
        profile = await self.get_profile(user_id, guild_id)
        return cosmetic_id in profile.unlocked_cosmetics
