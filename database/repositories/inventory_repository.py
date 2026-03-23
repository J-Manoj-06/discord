from datetime import datetime, timezone
from typing import Any, Dict, List

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError


class InventoryRepository:
    def __init__(self, db) -> None:
        self.collection = db["inventory"]

    async def ensure_indexes(self) -> None:
        await self.collection.create_index([("user_id", 1), ("guild_id", 1)], unique=True)

    async def create_indexes(self) -> None:
        await self.ensure_indexes()

    def _default_inventory(self, user_id: int, guild_id: int) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        return {
            "user_id": user_id,
            "guild_id": guild_id,
            "owned_item_ids": ["title:rookie", "theme:default", "vote_effect:default"],
            "created_at": now,
            "updated_at": now,
        }

    async def get_or_create_inventory(self, user_id: int, guild_id: int) -> Dict[str, Any]:
        inventory = await self.collection.find_one({"user_id": user_id, "guild_id": guild_id})
        if inventory:
            return inventory

        payload = self._default_inventory(user_id, guild_id)
        try:
            await self.collection.insert_one(payload)
            return payload
        except DuplicateKeyError:
            return await self.collection.find_one({"user_id": user_id, "guild_id": guild_id})

    async def add_item(self, user_id: int, guild_id: int, item_id: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        await self.get_or_create_inventory(user_id, guild_id)
        return await self.collection.find_one_and_update(
            {"user_id": user_id, "guild_id": guild_id},
            {"$addToSet": {"owned_item_ids": item_id}, "$set": {"updated_at": now}},
            return_document=ReturnDocument.AFTER,
        )

    async def has_item(self, user_id: int, guild_id: int, item_id: str) -> bool:
        inventory = await self.get_or_create_inventory(user_id, guild_id)
        return item_id in inventory.get("owned_item_ids", [])

    async def get_items(self, user_id: int, guild_id: int) -> List[str]:
        inventory = await self.get_or_create_inventory(user_id, guild_id)
        return inventory.get("owned_item_ids", [])

    async def add_cosmetic(self, user_id: int, guild_id: int, cosmetic_id: str, category: str) -> bool:
        """Add cosmetic to inventory."""
        now = datetime.now(timezone.utc)
        result = await self.collection.update_one(
            {"user_id": user_id, "guild_id": guild_id},
            {"$addToSet": {"owned_item_ids": cosmetic_id}, "$set": {"updated_at": now}},
        )
        return result.modified_count > 0 or result.matched_count > 0

    async def has_cosmetic(self, user_id: int, guild_id: int, cosmetic_id: str, category: str) -> bool:
        """Check if user owns a cosmetic."""
        inventory = await self.get_or_create_inventory(user_id, guild_id)
        return cosmetic_id in inventory.get("owned_item_ids", [])

    async def set_equipped_effect(self, user_id: int, guild_id: int, effect_id: str) -> bool:
        """Set equipped vote effect."""
        now = datetime.now(timezone.utc)
        doc = await self.collection.find_one({"user_id": user_id, "guild_id": guild_id})
        
        if not doc:
            await self.get_or_create_inventory(user_id, guild_id)
        
        result = await self.collection.update_one(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"equipped_vote_effect": effect_id, "updated_at": now}},
        )
        return result.modified_count > 0 or result.matched_count > 0

    async def get_equipped_effect(self, user_id: int, guild_id: int) -> str:
        """Get user's equipped vote effect."""
        inventory = await self.get_or_create_inventory(user_id, guild_id)
        return inventory.get("equipped_vote_effect", "default")

    async def create_indexes(self):
        """Create database indexes."""
        await self.collection.create_index([("user_id", 1), ("guild_id", 1)], unique=True)
