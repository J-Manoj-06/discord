"""
Vote Effect Service: Manages cosmetic voting effect selection and rendering.
Provides visual customization for vote messages without affecting game logic.
"""
import logging
from typing import Optional

from database.repositories.inventory_repository import InventoryRepository
from models.cosmetic_item import CosmeticItem, VoteEffect

logger = logging.getLogger(__name__)

# Pre-defined vote effects catalog
VOTE_EFFECTS_CATALOG = {
    "default": CosmeticItem(
        id="default",
        name="Default Vote",
        category="vote_effect",
        price_coins=0,
        description="Standard vote display",
        rarity="common",
        unlock_type="default",
    ),
    "dramatic": CosmeticItem(
        id="dramatic",
        name="Dramatic Vote",
        category="vote_effect",
        price_coins=200,
        description="💥 Vote with dramatic flair! 💥",
        rarity="common",
        unlock_type="purchase",
    ),
    "stylish": CosmeticItem(
        id="stylish",
        name="Stylish Vote",
        category="vote_effect",
        price_coins=300,
        description="✨ Clean and sleek vote display ✨",
        rarity="uncommon",
        unlock_type="purchase",
    ),
    "fire": CosmeticItem(
        id="fire",
        name="Fire Vote",
        category="vote_effect",
        price_coins=400,
        description="🔥 Scorching hot vote! 🔥",
        rarity="uncommon",
        unlock_type="purchase",
    ),
    "shadow": CosmeticItem(
        id="shadow",
        name="Shadow Vote",
        category="vote_effect",
        price_coins=500,
        description="🌑 Vote from the shadows... 🌑",
        rarity="rare",
        unlock_type="purchase",
    ),
    "royal": CosmeticItem(
        id="royal",
        name="Royal Vote",
        category="vote_effect",
        price_coins=600,
        description="👑 Regal and commanding vote 👑",
        rarity="rare",
        unlock_type="purchase",
    ),
    "glitch": CosmeticItem(
        id="glitch",
        name="Glitch Vote",
        category="vote_effect",
        price_coins=400,
        description="▯ G1̸͜7̶C̸H ͇V̘͜O͎T̡́E̶ ▯",
        rarity="rare",
        unlock_type="purchase",
    ),
    "neon": CosmeticItem(
        id="neon",
        name="Neon Vote",
        category="vote_effect",
        price_coins=500,
        description="⚡ Cyberpunk neon vibes ⚡",
        rarity="rare",
        unlock_type="purchase",
    ),
    "premium_gold": CosmeticItem(
        id="premium_gold",
        name="Premium Gold Vote",
        category="vote_effect",
        price_gems=100,
        description="⭐ Exclusive premium voting ⭐",
        rarity="epic",
        unlock_type="gems",
    ),
}


class VoteEffectService:
    """Service for managing user vote effects and cosmetics."""

    def __init__(self, inventory_repo: InventoryRepository):
        self.inventory_repo = inventory_repo

    def get_effect_catalog(self) -> dict:
        """Get all available vote effects."""
        return VOTE_EFFECTS_CATALOG.copy()

    def get_effect(self, effect_id: str) -> Optional[CosmeticItem]:
        """Get a specific vote effect by ID."""
        return VOTE_EFFECTS_CATALOG.get(effect_id)

    def list_purchasable_effects(self) -> list:
        """Get list of purchasable vote effects for the shop."""
        return [e for e in VOTE_EFFECTS_CATALOG.values() if e.id != "default"]

    async def unlock_effect(
        self, user_id: int, guild_id: int, effect_id: str
    ) -> bool:
        """Unlock (purchase) a vote effect for a user."""
        if effect_id not in VOTE_EFFECTS_CATALOG:
            logger.warning(f"Invalid effect ID: {effect_id}")
            return False

        return await self.inventory_repo.add_cosmetic(
            user_id, guild_id, effect_id, "vote_effect"
        )

    async def equip_effect(
        self, user_id: int, guild_id: int, effect_id: str
    ) -> bool:
        """Equip a vote effect."""
        if effect_id not in VOTE_EFFECTS_CATALOG:
            logger.warning(f"Invalid effect ID: {effect_id}")
            return False

        # Check ownership (except for "default")
        if effect_id != "default":
            has_effect = await self.inventory_repo.has_cosmetic(
                user_id, guild_id, effect_id, "vote_effect"
            )
            if not has_effect:
                logger.warning(
                    f"User {user_id} tried to equip effect {effect_id} they don't own"
                )
                return False

        return await self.inventory_repo.set_equipped_effect(
            user_id, guild_id, effect_id
        )

    async def get_equipped_effect(self, user_id: int, guild_id: int) -> str:
        """Get user's equipped vote effect."""
        effect = await self.inventory_repo.get_equipped_effect(user_id, guild_id)
        return effect if effect else "default"

    async def render_vote(
        self, user_id: int, guild_id: int, voter_name: str, target_name: str
    ) -> str:
        """
        Render a vote message with the user's equipped effect.
        Returns formatted vote message string.
        """
        effect_id = await self.get_equipped_effect(user_id, guild_id)
        effect = self.get_effect(effect_id)

        if effect_id == "default" or not effect:
            return f"{voter_name} votes for {target_name} 🗳️"

        # Render based on effect type
        templates = {
            "dramatic": f"💥 **{voter_name}** DRAMATICALLY VOTES for **{target_name}** 💥",
            "stylish": f"✨ *{voter_name}* elegantly votes for *{target_name}* ✨",
            "fire": f"🔥 **{voter_name}** BURNS A VOTE on **{target_name}** 🔥",
            "shadow": f"🌑 *{voter_name} votes from the shadows for {target_name}* 🌑",
            "royal": f"👑 **{voter_name}** DECREES: **{target_name}** 👑",
            "glitch": f"▯ {voter_name} V̸O̸T̸E̸S {target_name} ▯",
            "neon": f"⚡ >>> {voter_name} >> VOTES >> {target_name} <<< ⚡",
            "premium_gold": f"⭐ ✨**{voter_name}** PREMIUM VOTES FOR **{target_name}**✨ ⭐",
        }

        return templates.get(effect_id, f"{voter_name} votes for {target_name} 🗳️")

    async def preview_effect(self, effect_id: str) -> str:
        """Preview what an effect looks like."""
        if effect_id not in VOTE_EFFECTS_CATALOG:
            return "Unknown effect"

        effect = self.get_effect(effect_id)
        preview_voter = "ExampleUser"
        preview_target = "VotedPlayer"

        templates = {
            "default": f"{preview_voter} votes for {preview_target} 🗳️",
            "dramatic": f"💥 **{preview_voter}** DRAMATICALLY VOTES for **{preview_target}** 💥",
            "stylish": f"✨ *{preview_voter}* elegantly votes for *{preview_target}* ✨",
            "fire": f"🔥 **{preview_voter}** BURNS A VOTE on **{preview_target}** 🔥",
            "shadow": f"🌑 *{preview_voter} votes from the shadows for {preview_target}* 🌑",
            "royal": f"👑 **{preview_voter}** DECREES: **{preview_target}** 👑",
            "glitch": f"▯ {preview_voter} V̸O̸T̸E̸S {preview_target} ▯",
            "neon": f"⚡ >>> {preview_voter} >> VOTES >> {preview_target} <<< ⚡",
            "premium_gold": f"⭐ ✨**{preview_voter}** PREMIUM VOTES FOR **{preview_target}**✨ ⭐",
        }

        return templates.get(effect_id, f"{preview_voter} votes for {preview_target}")

