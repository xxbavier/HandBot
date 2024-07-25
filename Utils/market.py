import discord
from discord import app_commands
from discord.ext import commands

class MarketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_member_remove(self, member: discord.RawMemberRemoveEvent):
        if member.

    @app_commands.guild_only()
    class MarketGroup(commands.Group):
        pass

async def setup(bot: commands.Bot):
    await bot.add_cog(MarketCog(bot=bot))