"""Bot-owned MongoDB access; network calls never run on the Discord loop."""

import asyncio
from typing import Any

from pymongo import MongoClient

from settings import ConfigurationError

DATABASE_NAMES = {
    "Player Data": "Player_Data",
    "Contracts": "Contracts",
    "Demands": "Demands",
    "Season Info": "SeasonInfo",
    "Subscriptions": "Subscriptions",
}


class Database:
    def __init__(self, uri: str | None):
        self._uri = uri
        self._client: MongoClient | None = None
        self._connect_lock = asyncio.Lock()

    async def connect(self) -> None:
        async with self._connect_lock:
            if self._client is not None:
                return
            if not self._uri:
                raise ConfigurationError(
                    "Database-backed extensions require MONGO_ACCESS or db_connection in config.json."
                )
            self._client = await asyncio.to_thread(self._open_client)

    def _open_client(self) -> MongoClient:
        client = MongoClient(
            self._uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
        )
        try:
            client.admin.command("ping")
        except Exception:
            client.close()
            raise
        return client

    async def find_one(self, database: str, collection: str, query: dict) -> Any:
        await self.connect()
        target = self._client[DATABASE_NAMES[database]][collection]
        return await asyncio.to_thread(target.find_one, query)

    async def update_one(
        self, database: str, collection: str, query: dict, update: dict,
        *, upsert: bool = False,
    ) -> Any:
        await self.connect()
        target = self._client[DATABASE_NAMES[database]][collection]
        return await asyncio.to_thread(target.update_one, query, update, upsert=upsert)

    async def close(self) -> None:
        async with self._connect_lock:
            if self._client is not None:
                client, self._client = self._client, None
                await asyncio.to_thread(client.close)
