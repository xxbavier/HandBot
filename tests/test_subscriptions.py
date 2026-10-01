import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from discord import app_commands

from Utils.admin import admin
from Utils.market import market, teamCheck, team_names
from Utils.subscriptions import subscribers


class SubscriptionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.database = SimpleNamespace(find_one=AsyncMock(), update_one=AsyncMock())
        self.group = subscribers(self.database)
        self.interaction = SimpleNamespace(
            user=SimpleNamespace(id=123),
            response=SimpleNamespace(defer=AsyncMock()),
            edit_original_response=AsyncMock(),
        )
        self.target = SimpleNamespace(name="Player", edit=AsyncMock())

    async def invoke(self):
        await self.group.nickname.callback(
            self.group, self.interaction, self.target, "New Nickname"
        )

    async def test_new_and_expired_cooldowns_write_the_collection_that_is_read(self):
        for cooldown in (None, {"SetTime": 0}):
            with self.subTest(cooldown=cooldown), \
                    patch("Utils.subscriptions.time.time", return_value=100000):
                self.database.find_one.return_value = cooldown
                self.database.update_one.reset_mock()
                await self.invoke()
                self.database.find_one.assert_awaited_with(
                    "Subscriptions", "NicknameCooldown", {"DiscordId": 123}
                )
                self.database.update_one.assert_awaited_once_with(
                    "Subscriptions", "NicknameCooldown", {"DiscordId": 123},
                    {"$set": {"SetTime": 100000}}, upsert=True,
                )
                self.target.edit.assert_awaited_with(nick="New Nickname")
                embed = self.interaction.edit_original_response.call_args.kwargs["embed"]
                self.assertEqual(embed.title, "Nickname changed!")

    async def test_active_cooldown_does_not_change_nickname(self):
        self.database.find_one.return_value = {"SetTime": 99999}
        with patch("Utils.subscriptions.time.time", return_value=100000):
            await self.invoke()
        self.target.edit.assert_not_awaited()
        self.database.update_one.assert_not_awaited()
        embed = self.interaction.edit_original_response.call_args.kwargs["embed"]
        self.assertEqual(embed.title, "Cannot change nickname!")

    async def test_exactly_24_hours_allows_change(self):
        self.database.find_one.return_value = {"SetTime": 100000 - 86400}
        with patch("Utils.subscriptions.time.time", return_value=100000):
            await self.invoke()
        self.target.edit.assert_awaited_once()

    async def test_acknowledges_before_database_work(self):
        async def lookup(*args):
            self.interaction.response.defer.assert_awaited_once_with(thinking=True)
            return None
        self.database.find_one.side_effect = lookup
        await self.invoke()

    async def test_failed_nickname_edit_does_not_consume_cooldown(self):
        self.database.find_one.return_value = None
        self.target.edit.side_effect = RuntimeError("edit failed")
        with self.assertRaises(RuntimeError):
            await self.invoke()
        self.database.update_one.assert_not_awaited()

    def test_existing_command_names_and_role_checks(self):
        self.assertEqual(self.group.name, "subscribers")
        self.assertEqual(self.group.nickname.name, "nickname")
        self.assertEqual(market().demand.name, "demand")
        self.assertEqual(admin().verdict.name, "verdict")
        for group, command, roles in (
            (self.group, "nickname", ("Silver Tier", "Gold Tier", "Diamond Tier")),
            (admin(), "verdict", ("Commissioner", "Director")),
        ):
            check = group.get_command(command).checks[0]
            for role in roles:
                inter = SimpleNamespace(user=SimpleNamespace(roles=[SimpleNamespace(name=role)]))
                self.assertTrue(check(inter))
            with self.assertRaises(app_commands.MissingAnyRole):
                check(SimpleNamespace(user=SimpleNamespace(roles=[])))

    def test_market_team_check_uses_existing_team_names(self):
        self.assertTrue(team_names)
        inter = SimpleNamespace(user=SimpleNamespace(roles=[SimpleNamespace(name=team_names[0])]))
        self.assertTrue(teamCheck(inter))
        self.assertFalse(teamCheck(SimpleNamespace(user=SimpleNamespace(roles=[]))))
