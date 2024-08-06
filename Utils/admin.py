import discord, time, datetime, math
from discord import app_commands
from discord.ext import commands
from database import databases

@app_commands.guild_only()
class admin(app_commands.Group):
    @app_commands.command()
    @app_commands.checks.has_any_role("Commissioner", "Director")
    async def verdict(self, inter: discord.Interaction, target: discord.Member, nickname: str):
        modal = discord.ui.Modal()
        modal.title = "Verdict Creator"
        #modal.

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot=bot))
    bot.tree.add_command(admin())