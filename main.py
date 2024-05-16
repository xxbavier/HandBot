import os
import discord
from discord import app_commands, ui
from typing import List
import threading
import random
import roblox
import json
import asyncio
from settings import htl_servers
from Modules.teamRoles import *
from Commands import admin
from inspect import getmembers, isfunction, isclass
from Modules.database import databases

try:
    token = os.environ['BOT_TOKEN']
except KeyError:
    with open("config.json", "r") as file:
        data = json.load(file)
        token = data["token"]
        mongoLogIn = data["db_connection"]

token: str
mongoLogIn: str

# Initiate
@bot.event
async def on_ready():
    print("Bot is up! Syncing now...")

    cmds = await bot.get_guild(htl_servers["League"]).integrations()

    syncedcommands = await bot.tree.sync()
    await bot.change_presence(status= discord.Status.online, activity= discord.Game("Handball"))

    commands_list = ""
    for cmd in syncedcommands:
        commands_list += "\n    - " + cmd.name

    print("Logged into {} and fully functional with the following commands: {}".format(bot.user.name, commands_list))

#bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    embed = discord.Embed(title="Error", description="There was an error when processing the command.", color=discord.Color.red())
    embed.add_field(name= "``Error Description``", value= "*"+str(error)+"*")

    await interaction.response.send_message(embed= embed, ephemeral=True)

bot.run(token= token)