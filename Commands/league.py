import discord
from discord import app_commands, ui
from settings import bot, htl_servers
from Modules.database import databases
from Modules.elo_system import new_rating, get_estimated_score, get_team_average
import roblox
import json
from Commands.teams import teams_autocomplete
from Modules.teamRoles import isTeamRole, getTeamAccounts
from Modules.RobloxCloud import DataStores
import time

resources = {
    "Group": "https://www.roblox.com/groups/33672778/National-Handball-Association-NHA#!/about",
    "Rulebook": "https://docs.google.com/document/d/1blgWUD2JOHCZrDZ_VmUtJwNbDsDhOW9H-1YslFCPBjg/edit#heading=h.n29msmna3upk",
    "Schedule": "https://docs.google.com/spreadsheets/d/1M5waYQpJjbPszYBXlSKQqdE1AJqv0IyZrN8gjcAVOoM/edit#gid=506776664",
    "Staff Applications": "https://forms.gle/ZZJCSNZ7KqpTmBBU9",
    "Stats": "https://docs.google.com/spreadsheets/d/1M5waYQpJjbPszYBXlSKQqdE1AJqv0IyZrN8gjcAVOoM/edit#gid=506776664"
}

async def resource_options(inter: discord.Integration, current: str):
    choices = []

    for resource in resources:
        choices.append(app_commands.Choice(name=resource, value=resource))

    return choices

@app_commands.guild_only()
class league(app_commands.Group):
    @app_commands.command()
    @app_commands.autocomplete(resource= resource_options)
    async def resources(self, inter: discord.Interaction, resource: str):
        embed = discord.Embed()
        embed.title = "League Resource"
        embed.description = "Here is your requested league resource."
        
        view = ui.View()
        
        button = ui.Button(label=resource, url= resources[resource])
        view.add_item(button)

        await inter.response.send_message(embed= embed, view= view, ephemeral= True)
        


bot.tree.add_command(league())