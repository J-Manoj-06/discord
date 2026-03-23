"""
Shop Service: Manages catalog of cosmetic items and purchase validation.
Integrates with economy for transactions.
"""
import logging
from typing import Optional, Tuple

from database.repositories.inventory_repository import InventoryRepository
from models.cosmetic_item import CosmeticItem

logger = logging.getLogger(__name__)

# Complete shop catalog
SHOP_CATALOG = {
    # Vote Effects
    "default_vote": CosmeticItem(
        id="default_vote",
        name="Default Vote",
        category="vote_effect",
        price_coins=0,
        description="Standard vote display",
        rarity="common",
        unlock_type="default",
    ),
    "dramatic_vote": CosmeticItem(
        id="dramatic_vote",
        name="Dramatic Vote",
        category="vote_effect",
        price_coins=200,
        description="💥 Vote with dramatic flair!",
        rarity="common",
        unlock_type="purchase",
    ),
    "stylish_vote": CosmeticItem(
        id="stylish_vote",
        name="Stylish Vote",
        category="vote_effect",
        price_coins=300,
        description="✨ Clean and sleek vote display",
        rarity="uncommon",
        unlock_type="purchase",
    ),
    "fire_vote": CosmeticItem(
        id="fire_vote",
        name="Fire Vote",
        category="vote_effect",
        price_coins=400,
        description="🔥 Scorching hot vote!",
        rarity="uncommon",
        unlock_type="purchase",
    ),
    "shadow_vote": CosmeticItem(
        id="shadow_vote",
        name="Shadow Vote",
        category="vote_effect",
        price_coins=500,
        description="🌑 Vote from the shadows",
        rarity="rare",
        unlock_type="purchase",
    ),
    "royal_vote": CosmeticItem(
        id="royal_vote",
        name="Royal Vote",
        category="vote_effect",
        price_coins=600,
        description="👑 Regal and commanding vote",
        rarity="rare",
        unlock_type="purchase",
    ),
    "glitch_vote": CosmeticItem(
        id="glitch_vote",
        name="Glitch Vote",
        category="vote_effect",
        price_coins=400,
        description="▯ G1̸C̸H ͇V̸O̸T̸E ▯",
        rarity="rare",
        unlock_type="purchase",
    ),
    "neon_vote": CosmeticItem(
        id="neon_vote",
        name="Neon Vote",
        category="vote_effect",
        price_coins=500,
        description="⚡ Cyberpunk neon vibes",
        rarity="rare",
        unlock_type="purchase",
    ),
    "premium_gold_vote": CosmeticItem(
        id="premium_gold_vote",
        name="Premium Gold Vote",
        category="vote_effect",
        price_gems=100,
        description="⭐ Exclusive premium voting",
        rarity="epic",
        unlock_type="gems",
    ),
    # Titles
    "rookie_title": CosmeticItem(
        id="rookie_title",
        name="Rookie",
        category="title",
        price_coins=0,
        description="Starter title for all players",
        rarity="common",
        unlock_type="default",
    ),
    "detective_mind_title": CosmeticItem(
        id="detective_mind_title",
        name="Detective Mind",
        category="title",
        price_coins=250,
        description="For clever strategists",
        rarity="uncommon",
        unlock_type="purchase",
    ),
    "night_hunter_title": CosmeticItem(
        id="night_hunter_title",
        name="Night Hunter",
        category="title",
        price_coins=400,
        description="For relentless mafia players",
        rarity="rare",
        unlock_type="purchase",
    ),
    "town_hero_title": CosmeticItem(
        id="town_hero_title",
        name="Town Hero",
        category="title",
        price_gems=50,
        description="Prestige title for protectors",
        rarity="epic",
        unlock_type="gems",
    ),
    # Themes
    "classic_theme": CosmeticItem(
        id="classic_theme",
        name="Classic Theme",
        category="theme",
        price_coins=0,
        description="Default profile theme",
        rarity="common",
        unlock_type="default",
    ),
    "midnight_theme": CosmeticItem(
        id="midnight_theme",
        name="Midnight Theme",
        category="theme",
        price_coins=300,
        description="Deep blue profile style",
        rarity="uncommon",
        unlock_type="purchase",
    ),
    "ember_theme": CosmeticItem(
        id="ember_theme",
        name="Ember Theme",
        category="theme",
        price_coins=400,
        description="Warm fire profile style",
        rarity="rare",
        unlock_type="purchase",
    ),
    "aurora_theme": CosmeticItem(
        id="aurora_theme",
        name="Aurora Theme",
        category="theme",
        price_gems=75,
        description="Premium aurora profile style",
        rarity="epic",
        unlock_type="gems",
    ),
}


class ShopService:
    """Service for managing shop catalog and purchases."""

    def __init__(self, inventory_repo: InventoryRepository):
        self.inventory_repo = inventory_repo

    def get_catalog(self) -> dict:
        """Get entire catalog."""
        return SHOP_CATALOG.copy()

    def get_item(self, item_id: str) -> Optional[CosmeticItem]:
        """Get item by ID."""
        return SHOP_CATALOG.get(item_id)

    def list_by_category(self, category: str) -> list:
        """List items by category (vote_effect, title, theme)."""
        return [i for i in SHOP_CATALOG.values() if i.category == category]

    def list_purchasable(self) -> list:
        """Get all purchasable items for shop."""
        return [i for i in SHOP_CATALOG.values() if i.id != "classic_theme" and i.id != "default_vote" and i.id != "rookie_title"]

    async def purchase_item(
        self,
        user_id: int,
        guild_id: int,
        item_id: str,
        user_coins: int,
        user_gems: int,
    ) -> Tuple[bool, str]:
        """
        Validate purchase and process transaction.
        Returns (success, message).
        Economy service should handle actual coin/gem deduction.
        """
        item = self.get_item(item_id)
        if not item:
            return False, f"Item '{item_id}' not found in shop"

        # Check if user already owns (allow re-equip of default items)
        has_item = await self.inventory_repo.has_cosmetic(
            user_id, guild_id, item_id, item.category
        )
        if has_item and item.unlock_type != "default":
            return False, "You already own this item"

        # Check price and balance
        if item.price_coins > 0:
            if user_coins < item.price_coins:
                return False, f"Need {item.price_coins} coins, you have {user_coins}"
            return True, "coin"

        if item.price_gems > 0:
            if user_gems < item.price_gems:
                return False, f"Need {item.price_gems} gems, you have {user_gems}"
            return True, "gem"

        return False, "Item has no price"

    def get_item_format(self, item: CosmeticItem) -> str:
        """Format item for display in shop list."""
        price_str = ""
        if item.price_coins > 0:
            price_str = f"{item.price_coins} coins"
        elif item.price_gems > 0:
            price_str = f"{item.price_gems} gems"
        else:
            price_str = "Free"

        rarity_emoji = {"common": "⚪", "uncommon": "🟢", "rare": "🔵", "epic": "🟣"}
        rarity_em = rarity_emoji.get(item.rarity, "⚪")

        return (
            f"{rarity_em} **{item.name}** ({item.category})\n"
            f"  Price: {price_str} | {item.description}"
        )

