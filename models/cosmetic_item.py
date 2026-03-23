

"""
Cosmetic Item Models: Data structures for cosmetics, titles, and effects.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CosmeticItem:
    """Represents a purchasable cosmetic item."""

    id: str
    name: str
    category: str  # vote_effect, title, theme
    price_coins: int = 0
    description: str = ""
    rarity: str = "common"  # common, uncommon, rare, epic
    unlock_type: str = "purchase"  # purchase, gems, default
    price_gems: int = 0
    min_level: Optional[int] = None


@dataclass(frozen=True)
class VoteEffect:
    """Represents a voting effect cosmetic."""

    id: str
    name: str
    description: str
    price_coins: int
    price_gems: int
    rarity: str
