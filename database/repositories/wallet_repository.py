from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pymongo import DESCENDING, ReturnDocument
from pymongo.errors import DuplicateKeyError

from models.wallet import Wallet


class WalletRepository:
    def __init__(self, db) -> None:
        self.collection = db["wallets"]

    async def create_indexes(self) -> None:
        await self.collection.create_index([("user_id", 1), ("guild_id", 1)], unique=True)
        await self.collection.create_index([("guild_id", 1), ("coins", DESCENDING)])
        await self.collection.create_index([("guild_id", 1), ("total_wins", DESCENDING)])

    async def ensure_indexes(self) -> None:
        await self.create_indexes()

    def _default_wallet(self, user_id: int, guild_id: int) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        return {
            "user_id": user_id,
            "guild_id": guild_id,
            "coins": 0,
            "gems": 0,
            "total_wins": 0,
            "total_losses": 0,
            "games_played": 0,
            "votes_cast": 0,
            "created_at": now,
            "last_daily_claim": None,
        }

    async def create(self, user_id: int, guild_id: int) -> Wallet:
        payload = self._default_wallet(user_id, guild_id)
        try:
            await self.collection.insert_one(payload)
        except DuplicateKeyError:
            pass
        return await self.find_by_user_guild(user_id, guild_id)

    async def get_or_create_wallet(self, user_id: int, guild_id: int) -> Dict[str, Any]:
        doc = await self.collection.find_one({"user_id": user_id, "guild_id": guild_id})
        if doc:
            return doc
        return self._default_wallet(user_id, guild_id) if not await self.collection.insert_one(self._default_wallet(user_id, guild_id)) else await self.collection.find_one({"user_id": user_id, "guild_id": guild_id})

    async def find_by_user_guild(self, user_id: int, guild_id: int) -> Optional[Wallet]:
        doc = await self.collection.find_one({"user_id": user_id, "guild_id": guild_id})
        if not doc:
            return None
        return Wallet(
            user_id=doc["user_id"],
            guild_id=doc["guild_id"],
            coins=doc.get("coins", 0),
            gems=doc.get("gems", 0),
            total_wins=doc.get("total_wins", 0),
            total_losses=doc.get("total_losses", 0),
            games_played=doc.get("games_played", 0),
            votes_cast=doc.get("votes_cast", 0),
            created_at=doc.get("created_at"),
            last_daily_claim=doc.get("last_daily_claim"),
        )

    async def update_coins(self, user_id: int, guild_id: int, amount: int) -> bool:
        result = await self.collection.update_one(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"coins": max(0, amount)}},
            upsert=True,
        )
        return result.acknowledged

    async def update_gems(self, user_id: int, guild_id: int, amount: int) -> bool:
        result = await self.collection.update_one(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"gems": max(0, amount)}},
            upsert=True,
        )
        return result.acknowledged

    async def update_last_daily_claim(self, user_id: int, guild_id: int) -> bool:
        now = datetime.now(timezone.utc)
        result = await self.collection.update_one(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"last_daily_claim": now}},
            upsert=True,
        )
        return result.acknowledged

    async def update_total_wins(self, user_id: int, guild_id: int, wins: int) -> bool:
        result = await self.collection.update_one(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"total_wins": max(0, wins)}},
            upsert=True,
        )
        return result.acknowledged

    async def update_total_losses(self, user_id: int, guild_id: int, losses: int) -> bool:
        result = await self.collection.update_one(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"total_losses": max(0, losses)}},
            upsert=True,
        )
        return result.acknowledged

    async def update_games_played(self, user_id: int, guild_id: int, games: int) -> bool:
        result = await self.collection.update_one(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"games_played": max(0, games)}},
            upsert=True,
        )
        return result.acknowledged

    async def find_top_by_coins(self, guild_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"guild_id": guild_id}).sort("coins", DESCENDING).limit(limit)
        return await cursor.to_list(length=limit)

    async def find_top_by_wins(self, guild_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"guild_id": guild_id}).sort("total_wins", DESCENDING).limit(limit)
        return await cursor.to_list(length=limit)

    # Compatibility methods
    async def top_by_coins(self, guild_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        return await self.find_top_by_coins(guild_id, limit)

    async def top_by_wins(self, guild_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        return await self.find_top_by_wins(guild_id, limit)

    async def can_afford(self, user_id: int, guild_id: int, coin_amount: int = 0, gem_amount: int = 0) -> bool:
        wallet = await self.find_by_user_guild(user_id, guild_id)
        if not wallet:
            wallet = await self.create(user_id, guild_id)
        return wallet.coins >= coin_amount and wallet.gems >= gem_amount

    async def add_coins(self, user_id: int, guild_id: int, amount: int) -> Dict[str, Any]:
        return await self.collection.find_one_and_update(
            {"user_id": user_id, "guild_id": guild_id},
            {"$inc": {"coins": amount}, "$setOnInsert": self._default_wallet(user_id, guild_id)},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def remove_coins(self, user_id: int, guild_id: int, amount: int) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one_and_update(
            {"user_id": user_id, "guild_id": guild_id, "coins": {"$gte": amount}},
            {"$inc": {"coins": -amount}},
            return_document=ReturnDocument.AFTER,
        )

    async def add_gems(self, user_id: int, guild_id: int, amount: int) -> Dict[str, Any]:
        return await self.collection.find_one_and_update(
            {"user_id": user_id, "guild_id": guild_id},
            {"$inc": {"gems": amount}, "$setOnInsert": self._default_wallet(user_id, guild_id)},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def increment_votes_cast(self, user_id: int, guild_id: int) -> Dict[str, Any]:
        return await self.collection.find_one_and_update(
            {"user_id": user_id, "guild_id": guild_id},
            {"$inc": {"votes_cast": 1}, "$setOnInsert": self._default_wallet(user_id, guild_id)},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def set_last_daily_claim(self, user_id: int, guild_id: int, claim_time: datetime) -> Dict[str, Any]:
        return await self.collection.find_one_and_update(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"last_daily_claim": claim_time}, "$setOnInsert": self._default_wallet(user_id, guild_id)},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def update_game_stats(
        self,
        user_id: int,
        guild_id: int,
        won: bool,
        games_played_inc: int = 1,
        votes_cast_inc: int = 0,
    ) -> Dict[str, Any]:
        return await self.collection.find_one_and_update(
            {"user_id": user_id, "guild_id": guild_id},
            {
                "$inc": {
                    "games_played": games_played_inc,
                    "total_wins": 1 if won else 0,
                    "total_losses": 0 if won else 1,
                    "votes_cast": votes_cast_inc,
                },
                "$setOnInsert": self._default_wallet(user_id, guild_id),
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
