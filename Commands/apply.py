import discord
from discord import app_commands, ui
from settings import bot
from Modules.database import databases

applications_channel = bot.get_channel(1096067306133659790)

async def applications(inter: discord.Integration, current: str):
    positions = [pos for pos in applications_channel.available_tags if not pos.moderated]
    
    choices = []

    for position in positions:
        choices.append(app_commands.Choice(name=position.name, value=position.name))

    return choices

@bot.tree.command()
@app_commands.autocomplete(position= applications)
async def apply(inter: discord.Interaction, position: str):
    threads = [thread for thread in applications_channel.threads if app_commands.Choice(name= position, value= position) in thread.applied_tags]

    for thread in threads:
        pass
        #if thread.

    profile = databases["Player Data"]["Careers"].find_one({"DiscordId": inter.user.id})

    class application(ui.Modal):
        def __init__(self, *, title: str = ..., custom_id: str = ...) -> None:
            super().__init__(title=title, timeout= None, custom_id= f"apply {position}")

    if position == "Team Owner":
        
        has_played = ui.TextInput(label= "Have you played in HTL before?")