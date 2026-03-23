from datetime import datetime, timezone
from typing import Any, Dict, Optional, List

from pymongo import DESCENDING


class EconomyLogRepository:
    def __init__(self, db) -> None:
        self.collection = db["economy_logs"]

    async def create_indexes(self) -> None:
        await self.collection.create_index([("guild_id", 1), ("user_id", 1), ("created_at", DESCENDING)])
        await self.collection.create_index([("user_id", 1), ("guild_id", 1), ("created_at", DESCENDING)])

    async def ensure_indexes(self) -> None:
        await self.create_indexes()

    async def log_transaction(
        self,
        user_id: int,
        guild_id: int,
        tx_type: str,
        amount: int = 0,
        reason: str = "",
    ) -> None:
        now = datetime.now(timezone.utc)
        payload = {
            "user_id": user_id,
            "guild_id": guild_id,
            "tx_type": tx_type,
            "amount": amount,
            "reason": reason,
            "created_at": now,
        }
        await self.collection.insert_one(payload)

    async def find_by_user_guild(self, user_id: int, guild_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        cursor = self.collection.find(
            {"user_id": user_id, "guild_id": guild_id}
        ).sort("created_at", DESCENDING).limit(limit)
        return await cursor.to_list(length=limit)
