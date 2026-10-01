import discord
from discord import app_commands
from discord.ext import commands

from settings import ROOT

team_names = [
    line.strip()
    for line in (ROOT / "team names.txt").read_text(encoding="utf-8").splitlines()
]


def teamCheck(inter: discord.Interaction) -> bool:
    return any(role.name in team_names for role in getattr(inter.user, "roles", ()))


@app_commands.guild_only()
class market(app_commands.Group):
    @app_commands.command()
    @app_commands.check(teamCheck)
    async def demand(self, inter: discord.Interaction) -> None:
        await inter.response.send_message("Hello!")


class MarketCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MarketCog(bot=bot))
    bot.tree.add_command(market())


async def teardown(bot: commands.Bot) -> None:
    bot.tree.remove_command("market")
