"""Mafia Game Stats Repository: MongoDB operations for game statistics."""

from typing import Dict, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase


class MafiaGameStatsRepository:
    """Repository for Mafia game statistics and profiles."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize mafia game stats repository.
        
        Args:
            db: Motor async MongoDB database instance
        """
        self.db = db
        self.collection = db["mafia_game_stats"]

    async def initialize(self):
        """Initialize collection with indexes."""
        await self.collection.create_index("user_id", unique=True)

    async def get_stats(self, user_id: int) -> Optional[Dict]:
        """Get player game stats by user ID.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            Stats dict or None if not found
        """
        stats = await self.collection.find_one({"user_id": user_id})
        return stats

    async def create_stats(self, user_id: int) -> Dict:
        """Create new player game stats.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            New stats dict
        """
        stats = {
            "user_id": user_id,
            "games_played": 0,
            "wins": 0,
            "losses": 0,
            "last_role": None,
        }

        await self.collection.insert_one(stats)
        return stats

    async def get_or_create_stats(self, user_id: int) -> Dict:
        """Get stats or create if doesn't exist.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            Existing or new stats dict
        """
        stats = await self.get_stats(user_id)
        if stats is None:
            stats = await self.create_stats(user_id)
        return stats

    async def increment_game_played(self, user_id: int):
        """Increment games played counter.
        
        Args:
            user_id: Discord user ID
        """
        await self.collection.find_one_and_update(
            {"user_id": user_id},
            {"$inc": {"games_played": 1}},
            upsert=False,
        )

    async def increment_win(self, user_id: int):
        """Increment wins and games played.
        
        Args:
            user_id: Discord user ID
        """
        await self.collection.find_one_and_update(
            {"user_id": user_id},
            {
                "$inc": {
                    "wins": 1,
                    "games_played": 1,
                }
            },
            upsert=False,
        )

    async def increment_loss(self, user_id: int):
        """Increment losses and games played.
        
        Args:
            user_id: Discord user ID
        """
        await self.collection.find_one_and_update(
            {"user_id": user_id},
            {
                "$inc": {
                    "losses": 1,
                    "games_played": 1,
                }
            },
            upsert=False,
        )

    async def update_last_role(self, user_id: int, role: str) -> Dict:
        """Update last role played.
        
        Args:
            user_id: Discord user ID
            role: Role name (godfather, doctor, detective, villager)
            
        Returns:
            Updated stats dict
        """
        stats = await self.collection.find_one_and_update(
            {"user_id": user_id},
            {"$set": {"last_role": role}},
            return_document=True,
            upsert=False,
        )
        return stats

    async def batch_increment_wins(self, user_ids: list):
        """Batch increment wins for multiple players.
        
        Args:
            user_ids: List of user IDs who won
        """
        if not user_ids:
            return

        await self.collection.update_many(
            {"user_id": {"$in": user_ids}},
            {
                "$inc": {
                    "wins": 1,
                    "games_played": 1,
                }
            },
            upsert=False,
        )

    async def batch_increment_losses(self, user_ids: list):
        """Batch increment losses for multiple players.
        
        Args:
            user_ids: List of user IDs who lost
        """
        if not user_ids:
            return

        await self.collection.update_many(
            {"user_id": {"$in": user_ids}},
            {
                "$inc": {
                    "losses": 1,
                    "games_played": 1,
                }
            },
            upsert=False,
        )
