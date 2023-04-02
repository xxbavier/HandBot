import discord
from discord import app_commands
from Modules.database import databases
from settings import bot

@app_commands.guild_only()
class medals(app_commands.Group, name= "medals"):
    @app_commands.command(description="View a player's medals.")
    async def view(self, inter: discord.interactions.Interaction, member: discord.User):
        embed = discord.Embed(title= "{}'s Awards".format(member.name), color=member.color)
        embed.description = "Loading..."
        await inter.response.send_message(embed= embed)

        data = databases["Player Data"][str(member.id)]

        hb_rings = "No Rings"
        tournament_rings = "No Rings"

        for doc in data.find({}):
            if doc["handbowl_rings"]:
                if len(doc["handbowl_rings"]) <= 1:
                    hb_rings = ""

                    for ring in doc["handbowl_rings"]:
                        hb_rings += ring + "\n"

                
            elif doc["tournament_rings"]:
                if len(doc["tournament_rings"]) <= 1:
                    tournament_rings = ""
                    
                    for ring in doc["tournament_rings"]:
                        tournament_rings += ring + "\n"


        embed.add_field(name= "``Handbowl Rings``", value=hb_rings, inline=False)
        embed.add_field(name= "``Tournament Rings``", value=tournament_rings, inline=False)
        embed.add_field(name= "``Player Awards``", value="WIP", inline=False)
        embed.description = "Data loaded!"

        await inter.edit_original_response(embed=embed)

bot.tree.add_command(medals())