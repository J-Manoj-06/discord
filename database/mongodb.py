import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


logger = logging.getLogger(__name__)


class MongoDBClient:
    """MongoDB client wrapper used by repositories."""

    def __init__(self, uri: str, database_name: str = "discord_bot") -> None:
        self._uri = uri
        self._database_name = database_name
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        if self._client is not None:
            return

        self._client = AsyncIOMotorClient(self._uri)
        self._database = self._client[self._database_name]
        await self._client.admin.command("ping")
        logger.info("Connected to MongoDB database '%s'", self._database_name)

    @property
    def db(self) -> AsyncIOMotorDatabase:
        if self._database is None:
            raise RuntimeError("MongoDBClient is not connected")
        return self._database

    def __getitem__(self, collection_name: str):
        return self.db[collection_name]

    async def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("MongoDB connection closed")


# Backward-compatibility alias for existing imports.
MongoManager = MongoDBClient
