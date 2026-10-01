import asyncio
import threading
import unittest
from unittest.mock import MagicMock, patch

from database import Database
from settings import ConfigurationError


class DatabaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_missing_database_credentials_are_explicit(self):
        with self.assertRaisesRegex(ConfigurationError, "MONGO_ACCESS"):
            await Database(None).connect()

    async def test_no_connection_until_requested_and_connect_once(self):
        with patch("database.MongoClient") as factory:
            database = Database("mongodb://test")
            factory.assert_not_called()
            await asyncio.gather(database.connect(), database.connect())
            factory.assert_called_once()
            factory.return_value.admin.command.assert_called_once_with("ping")
            await database.close()
            await database.close()
            factory.return_value.close.assert_called_once()

    async def test_failed_ping_closes_client_and_allows_retry(self):
        with patch("database.MongoClient") as factory:
            factory.return_value.admin.command.side_effect = RuntimeError("unavailable")
            database = Database("mongodb://test")
            with self.assertRaises(RuntimeError):
                await database.connect()
            factory.return_value.close.assert_called_once()
            factory.return_value.admin.command.side_effect = None
            await database.connect()
            self.assertEqual(factory.call_count, 2)
            await database.close()

    async def test_database_operations_run_off_event_loop(self):
        loop_thread = threading.get_ident()
        worker_threads = []
        with patch("database.MongoClient") as factory:
            client = factory.return_value
            client.admin.command.side_effect = lambda *args: worker_threads.append(threading.get_ident())
            collection = MagicMock()
            client.__getitem__.return_value.__getitem__.return_value = collection
            collection.find_one.side_effect = lambda *args: worker_threads.append(threading.get_ident()) or {"SetTime": 1}
            collection.update_one.side_effect = lambda *args, **kwargs: worker_threads.append(threading.get_ident())
            database = Database("mongodb://test")
            result = await database.find_one("Subscriptions", "NicknameCooldown", {"DiscordId": 1})
            self.assertEqual(result, {"SetTime": 1})
            await database.update_one(
                "Subscriptions", "NicknameCooldown", {"DiscordId": 1},
                {"$set": {"SetTime": 2}}, upsert=True,
            )
            client.__getitem__.assert_called_with("Subscriptions")
            collection.update_one.assert_called_once_with(
                {"DiscordId": 1}, {"$set": {"SetTime": 2}}, upsert=True
            )
            self.assertEqual(len(worker_threads), 3)
            self.assertTrue(all(thread != loop_thread for thread in worker_threads))
            await database.close()
