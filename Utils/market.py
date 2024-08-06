import discord
from discord import app_commands
from discord.ext import commands

team_names = []

with open("team names.txt") as file:
    lines = file.readlines()

    for x in lines:
        team_names.append(x.strip())

def teamCheck(inter: discord.Interaction):
    for x in inter.user.roles:
        if x.name in team_names:
            return True
        
    return False

@app_commands.guild_only()
class market(app_commands.Group):
    @app_commands.command()
    @app_commands.check(teamCheck)
    async def demand(self, inter: discord.Interaction):
        await inter.response.send_message("Hello!")

class MarketCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_member_remove(self, member: discord.RawMemberRemoveEvent):
        pass

async def setup(bot: commands.Bot):
    await bot.add_cog(MarketCog(bot=bot))
    bot.tree.add_command(market())