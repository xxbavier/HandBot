import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import discord

from settings import MEMBER_LOG_CHANNEL_ID, WELCOME_INVITE
from Utils.member_setup import MemberSetup


class MemberSetupTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.channel = SimpleNamespace(send=AsyncMock())
        self.guild = SimpleNamespace(
            id=1, icon=None, member_count=42,
            get_channel=Mock(return_value=self.channel),
        )
        self.bot = SimpleNamespace(
            settings=SimpleNamespace(member_log_channel_id=MEMBER_LOG_CHANNEL_ID),
            get_guild=Mock(return_value=self.guild),
        )
        self.member = SimpleNamespace(
            id=2, guild=self.guild, mention="<@2>", send=AsyncMock()
        )
        self.cog = MemberSetup(self.bot)

    async def test_join_preserves_welcome_and_public_message(self):
        await self.cog.on_member_join(self.member)
        kwargs = self.member.send.call_args.kwargs
        self.assertEqual(kwargs["content"], WELCOME_INVITE)
        embed = kwargs["embed"]
        self.assertEqual(embed.title, "Welcome to *Handball: The League*.")
        self.assertEqual(len(embed.fields), 4)
        self.assertIn("5498056786", embed.fields[1].value)
        self.assertIn("1375158754529513484", embed.fields[2].value)
        self.guild.get_channel.assert_called_once_with(MEMBER_LOG_CHANNEL_ID)
        self.channel.send.assert_awaited_once_with(
            content="<:Green:1398092411842072708> | **<@2> has joined the server.** ``Members: 42``"
        )

    async def test_guild_icon_is_used_when_present(self):
        self.guild.icon = SimpleNamespace(url="https://example.com/icon.png")
        await self.cog.on_member_join(self.member)
        embed = self.member.send.call_args.kwargs["embed"]
        self.assertEqual(embed.thumbnail.url, self.guild.icon.url)

    async def test_blocked_dm_does_not_prevent_public_join_message(self):
        self.member.send.side_effect = discord.Forbidden(
            SimpleNamespace(status=403, reason="Forbidden"), "Cannot send messages"
        )
        with self.assertLogs("Utils.member_setup", level="WARNING"):
            await self.cog.on_member_join(self.member)
        self.channel.send.assert_awaited_once()

    async def test_leave_preserves_message(self):
        event = SimpleNamespace(guild_id=1, user=SimpleNamespace(name="Player"))
        await self.cog.on_raw_member_remove(event)
        self.channel.send.assert_awaited_once_with(
            content="<:Red:1398092453416009912> | *Player has left the server.*"
        )

    async def test_unavailable_guild_is_handled(self):
        self.bot.get_guild.return_value = None
        with self.assertLogs("Utils.member_setup", level="WARNING"):
            await self.cog.on_raw_member_remove(SimpleNamespace(guild_id=1))
        self.channel.send.assert_not_awaited()

    async def test_unavailable_channel_is_handled(self):
        self.guild.get_channel.return_value = None
        with self.assertLogs("Utils.member_setup", level="WARNING"):
            await self.cog.on_member_join(self.member)
        self.member.send.assert_awaited_once()
        self.channel.send.assert_not_awaited()

    async def test_channel_permission_failure_is_handled(self):
        self.channel.send.side_effect = discord.Forbidden(
            SimpleNamespace(status=403, reason="Forbidden"), "Missing permissions"
        )
        with self.assertLogs("Utils.member_setup", level="WARNING"):
            await self.cog.on_member_join(self.member)
