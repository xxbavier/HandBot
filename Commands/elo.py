import discord
from discord import app_commands
from Modules.elo_system import new_rating, get_estimated_score
from settings import bot

@app_commands.guild_only()
class elo(app_commands.Group):
    @app_commands.command()
    async def view(self, inter: discord.Interaction):
        pass

    @app_commands.command()
    async def test(self, inter: discord.Interaction):
        pass

    @app_commands.command()
    @app_commands.checks.has_role("Founder")
    async def update(self, team1: discord.Role, team2: discord.Role, winner: discord.Role):
        old_elos = {
            team1: 0,
            team2: 0
        }

        new_elos = {
            team1: new_rating(old_elos["team1"], old_elos["team2"], team1 == winner),
            team2: new_rating(old_elos["team2"], old_elos["team1"], team2 == winner)
        }

        confirmation = discord.Embed(title= "Elo Confirmation", description= "Are you sure you want to make this update?", color= discord.Color.yellow())
        confirmation.add_field(name= "``")

bot.tree.add_command(elo())