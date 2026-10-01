import importlib
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from discord import app_commands
from discord.ext import commands

from bot import HandBot
from settings import Settings


class BotTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bot = HandBot(Settings(token="test-token"))
        await self.bot.__aenter__()
        self.addAsyncCleanup(self.bot.close)

    async def test_startup_loads_current_extension_and_syncs_once(self):
        with patch.object(self.bot.tree, "sync", new=AsyncMock(return_value=[])) as sync:
            await self.bot.setup_hook()
            await self.bot.on_ready()
            await self.bot.on_ready()
        sync.assert_awaited_once_with()
        self.assertEqual(set(self.bot.extensions), {"Utils.member_setup"})
        self.assertIsNotNone(self.bot.get_cog("MemberSetup"))
        self.assertEqual(self.bot.tree.get_commands(), [])
        self.assertTrue(self.bot.intents.members)
        self.assertTrue(self.bot.intents.messages)
        self.assertTrue(self.bot.intents.message_content)
        self.assertIsNotNone(self.bot.get_command("help"))
        self.assertEqual(self.bot.command_prefix, "?")
        self.assertFalse(self.bot.intents.presences)
        self.assertEqual(self.bot.activity.name, "Handball")

    async def test_extension_failure_prevents_sync(self):
        with patch.object(self.bot, "load_extension", new=AsyncMock(side_effect=RuntimeError)), \
                patch.object(self.bot.tree, "sync", new=AsyncMock()) as sync:
            with self.assertRaises(RuntimeError):
                await self.bot.setup_hook()
        sync.assert_not_awaited()

    async def test_all_command_extensions_load_unload_and_reload(self):
        with patch.object(self.bot.database, "connect", new=AsyncMock()):
            for extension, group in (
                ("Utils.admin", "admin"),
                ("Utils.market", "market"),
                ("Utils.subscriptions", "subscribers"),
            ):
                with self.subTest(extension=extension):
                    await self.bot.load_extension(extension)
                    self.assertIsNotNone(self.bot.tree.get_command(group))
                    await self.bot.reload_extension(extension)
                    await self.bot.unload_extension(extension)
                    self.assertIsNone(self.bot.tree.get_command(group))

    async def test_close_cleans_up_database(self):
        with patch.object(self.bot.database, "close", new=AsyncMock()) as close:
            await self.bot.close()
        close.assert_awaited_once()

    async def test_importing_entry_point_does_not_start_bot(self):
        with patch.object(commands.Bot, "run") as run:
            import main
            importlib.reload(main)
        run.assert_not_called()

    def interaction(self, *, responded=False):
        return SimpleNamespace(
            command=None,
            response=SimpleNamespace(
                is_done=lambda: responded, send_message=AsyncMock()
            ),
            followup=SimpleNamespace(send=AsyncMock()),
        )

    async def test_permission_error_uses_initial_ephemeral_response(self):
        interaction = self.interaction()
        error = app_commands.MissingAnyRole(["Gold Tier"])
        await self.bot.tree.on_error(interaction, error)
        kwargs = interaction.response.send_message.call_args.kwargs
        self.assertTrue(kwargs["ephemeral"])
        self.assertIn("Gold Tier", kwargs["embed"].fields[0].value)
        interaction.followup.send.assert_not_awaited()

    async def test_deferred_error_uses_followup_and_hides_internal_details(self):
        interaction = self.interaction(responded=True)
        error = app_commands.CommandInvokeError(
            SimpleNamespace(name="test"), ValueError("internal-secret")
        )
        with self.assertLogs("bot", level="ERROR"):
            await self.bot.tree.on_error(interaction, error)
        interaction.response.send_message.assert_not_awaited()
        kwargs = interaction.followup.send.call_args.kwargs
        self.assertTrue(kwargs["ephemeral"])
        self.assertNotIn("internal-secret", str(kwargs["embed"].to_dict()))
