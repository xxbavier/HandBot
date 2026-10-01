"""Subscriber nickname command with a persisted 24-hour cooldown."""

import datetime
import math
import time

import discord
from discord import app_commands
from discord.ext import commands

from database import Database

COOLDOWN_SECONDS = 60 * 60 * 24


@app_commands.guild_only()
class subscribers(app_commands.Group):
    def __init__(self, database: Database):
        super().__init__()
        self.database = database

    @app_commands.command()
    @app_commands.checks.has_any_role("Silver Tier", "Gold Tier", "Diamond Tier")
    async def nickname(
        self, inter: discord.Interaction, target: discord.Member, nickname: str
    ) -> None:
        # Acknowledge before database/network work to avoid interaction timeouts.
        await inter.response.defer(thinking=True)
        query = {"DiscordId": inter.user.id}
        cooldown = await self.database.find_one("Subscriptions", "NicknameCooldown", query)
        now = time.time()

        if cooldown and now - cooldown["SetTime"] < COOLDOWN_SECONDS:
            remaining = datetime.timedelta(
                seconds=round(cooldown["SetTime"] + COOLDOWN_SECONDS - now)
            )
            embed = discord.Embed(
                title="Cannot change nickname!",
                description="You have already changed someone's nickname in the past 24 hours!",
                color=discord.Color.red(),
            )
            embed.add_field(name="Time Remaining", value=str(remaining))
            await inter.edit_original_response(embed=embed)
            return

        await target.edit(nick=nickname)
        # Read and write the same cooldown collection, for new and returning users.
        await self.database.update_one(
            "Subscriptions", "NicknameCooldown", query,
            {"$set": {"SetTime": math.floor(time.time())}}, upsert=True,
        )
        embed = discord.Embed(
            title="Nickname changed!",
            description="You have changed {}'s nickname, they are now {}!".format(target.name, nickname),
            color=discord.Color.green(),
        )
        await inter.edit_original_response(embed=embed)


class SubscriptionsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


async def setup(bot: commands.Bot) -> None:
    await bot.database.connect()
    await bot.add_cog(SubscriptionsCog(bot=bot))
    bot.tree.add_command(subscribers(bot.database))


async def teardown(bot: commands.Bot) -> None:
    bot.tree.remove_command("subscribers")
