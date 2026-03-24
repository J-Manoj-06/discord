from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from models.user_profile import UserProfile


class ProfileRepository:
    def __init__(self, db) -> None:
        self.collection = db["profiles"]

    async def create_indexes(self) -> None:
        await self.collection.create_index([("user_id", 1), ("guild_id", 1)], unique=True)
        await self.collection.create_index([("guild_id", 1), ("level", -1), ("xp", -1)])

    async def ensure_indexes(self) -> None:
        await self.create_indexes()

    def _default_profile(self, user_id: int, guild_id: int) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        return {
            "user_id": user_id,
            "guild_id": guild_id,
            "display_name": "Unknown",
            "avatar_url": "",
            "level": 1,
            "xp": 0,
            "wins": 0,
            "losses": 0,
            "games_played": 0,
            "equipped_title": None,
            "equipped_theme": "classic_theme",
            "votes_cast": 0,
            "unlocked_cosmetics": ["rookie_title", "classic_theme", "default_vote"],
            "favorite_role": None,
            "roles_played": {},
            "created_at": now,
            "updated_at": now,
        }

    async def create(self, user_id: int, guild_id: int) -> UserProfile:
        payload = self._default_profile(user_id, guild_id)
        try:
            await self.collection.insert_one(payload)
        except DuplicateKeyError:
            pass
        return await self.find_by_user_guild(user_id, guild_id)

    async def find_by_user_guild(self, user_id: int, guild_id: int) -> Optional[UserProfile]:
        doc = await self.collection.find_one({"user_id": user_id, "guild_id": guild_id})
        if not doc:
            return None
        return UserProfile(
            user_id=doc["user_id"],
            guild_id=doc["guild_id"],
            display_name=doc.get("display_name", "Unknown"),
            avatar_url=doc.get("avatar_url", ""),
            level=doc.get("level", 1),
            xp=doc.get("xp", 0),
            wins=doc.get("wins", 0),
            losses=doc.get("losses", 0),
            games_played=doc.get("games_played", 0),
            equipped_title=doc.get("equipped_title"),
            equipped_theme=doc.get("equipped_theme", "classic_theme"),
            votes_cast=doc.get("votes_cast", 0),
            unlocked_cosmetics=doc.get("unlocked_cosmetics", []),
            favorite_role=doc.get("favorite_role"),
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at"),
            roles_played=doc.get("roles_played", {}),
        )

    async def update_xp_and_level(self, user_id: int, guild_id: int, xp: int, level: int) -> bool:
        now = datetime.now(timezone.utc)
        result = await self.collection.update_one(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"xp": xp, "level": level, "updated_at": now}},
            upsert=True,
        )
        return result.acknowledged

    async def update_equipped_title(self, user_id: int, guild_id: int, title: str) -> bool:
        now = datetime.now(timezone.utc)
        result = await self.collection.update_one(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"equipped_title": title, "updated_at": now}},
            upsert=True,
        )
        return result.acknowledged

    async def update_equipped_theme(self, user_id: int, guild_id: int, theme: str) -> bool:
        now = datetime.now(timezone.utc)
        result = await self.collection.update_one(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"equipped_theme": theme, "updated_at": now}},
            upsert=True,
        )
        return result.acknowledged

    async def update_display_name(self, user_id: int, guild_id: int, name: str) -> bool:
        now = datetime.now(timezone.utc)
        result = await self.collection.update_one(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"display_name": name, "updated_at": now}},
            upsert=True,
        )
        return result.acknowledged

    async def update_favorite_role(self, user_id: int, guild_id: int, role: str) -> bool:
        now = datetime.now(timezone.utc)
        result = await self.collection.update_one(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"favorite_role": role, "updated_at": now}},
            upsert=True,
        )
        return result.acknowledged

    async def update_votes_cast(self, user_id: int, guild_id: int, count: int) -> bool:
        now = datetime.now(timezone.utc)
        result = await self.collection.update_one(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"votes_cast": count, "updated_at": now}},
            upsert=True,
        )
        return result.acknowledged

    async def update_unlocked_cosmetics(self, user_id: int, guild_id: int, cosmetics: list) -> bool:
        now = datetime.now(timezone.utc)
        result = await self.collection.update_one(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"unlocked_cosmetics": cosmetics, "updated_at": now}},
            upsert=True,
        )
        return result.acknowledged

    async def update_wins(self, user_id: int, guild_id: int, wins: int) -> bool:
        now = datetime.now(timezone.utc)
        result = await self.collection.update_one(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"wins": max(0, wins), "updated_at": now}},
            upsert=True,
        )
        return result.acknowledged

    async def update_losses(self, user_id: int, guild_id: int, losses: int) -> bool:
        now = datetime.now(timezone.utc)
        result = await self.collection.update_one(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"losses": max(0, losses), "updated_at": now}},
            upsert=True,
        )
        return result.acknowledged

    async def get_or_create_profile(
        self,
        user_id: int,
        guild_id: int,
        display_name: str = "Unknown",
        avatar_url: str = "",
    ) -> Dict[str, Any]:
        profile = await self.collection.find_one({"user_id": user_id, "guild_id": guild_id})
        if profile:
            return profile
        payload = self._default_profile(user_id, guild_id)
        payload["display_name"] = display_name
        payload["avatar_url"] = avatar_url
        try:
            await self.collection.insert_one(payload)
            return payload
        except DuplicateKeyError:
            return await self.collection.find_one({"user_id": user_id, "guild_id": guild_id})

    async def add_unlocked_cosmetic(self, user_id: int, guild_id: int, cosmetic_key: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        return await self.collection.find_one_and_update(
            {"user_id": user_id, "guild_id": guild_id},
            {
                "$addToSet": {"unlocked_cosmetics": cosmetic_key},
                "$set": {"updated_at": now},
                "$setOnInsert": self._default_profile(user_id, guild_id),
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def set_equipped_title(self, user_id: int, guild_id: int, title_id: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        return await self.collection.find_one_and_update(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"equipped_title": title_id, "updated_at": now}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def set_equipped_theme(self, user_id: int, guild_id: int, theme_id: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        return await self.collection.find_one_and_update(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"equipped_theme": theme_id, "updated_at": now}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def set_equipped_vote_effect(self, user_id: int, guild_id: int, effect_id: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        return await self.collection.find_one_and_update(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"selected_vote_effect": effect_id, "updated_at": now}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def set_favorite_role(self, user_id: int, guild_id: int, role_name: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        return await self.collection.find_one_and_update(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"favorite_role": role_name, "updated_at": now}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def add_xp(self, user_id: int, guild_id: int, amount: int) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        return await self.collection.find_one_and_update(
            {"user_id": user_id, "guild_id": guild_id},
            {
                "$inc": {"xp": amount},
                "$set": {"updated_at": now},
                "$setOnInsert": self._default_profile(user_id, guild_id),
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def set_level_and_xp(self, user_id: int, guild_id: int, level: int, xp: int) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        return await self.collection.find_one_and_update(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"level": level, "xp": xp, "updated_at": now}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def update_identity(self, user_id: int, guild_id: int, display_name: str, avatar_url: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        return await self.collection.find_one_and_update(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"display_name": display_name, "avatar_url": avatar_url, "updated_at": now}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def update_game_stats(self, user_id: int, guild_id: int, role: str, won: bool) -> Dict[str, Any]:
        """
        Update player stats after a game:
        - Increment games_played
        - Increment wins/losses based on outcome
        - Track role usage in roles_played
        """
        now = datetime.now(timezone.utc)
        
        # Prepare the update operations
        update_ops = {
            "$inc": {"games_played": 1},
            "$set": {"updated_at": now},
            "$setOnInsert": self._default_profile(user_id, guild_id),
        }
        
        # Increment wins or losses
        if won:
            update_ops["$inc"]["wins"] = 1
        else:
            update_ops["$inc"]["losses"] = 1
        
        # Track role usage
        role_key = f"roles_played.{role}"
        update_ops["$inc"][role_key] = 1
        
        # Update stats
        return await self.collection.find_one_and_update(
            {"user_id": user_id, "guild_id": guild_id},
            update_ops,
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def get_favorite_role(self, user_id: int, guild_id: int) -> Optional[str]:
        """
        Calculate and return the favorite role (most played role).
        """
        profile = await self.find_by_user_guild(user_id, guild_id)
        if not profile or not profile.roles_played:
            return None
        
        favorite = max(profile.roles_played, key=profile.roles_played.get)
        return favorite if favorite else None
