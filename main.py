import os, sys, traceback
import discord
from discord.ext import commands
from discord import app_commands, ui
import roblox
import json
from settings import htl_servers
import asyncio
import pprint

# Load Secrets
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
bot = commands.Bot(command_prefix= "?", intents=discord.Intents.all(), application_id= 885266060796899329)
roClient = roblox.Client()

# Load Extensions
extensions = [
    "Utils.member_setup",
    "Utils.subscriptions",
   # "Utils.market"
]

for ext in extensions:
    try:
        asyncio.run(bot.load_extension(ext))
    except Exception as e:
        print(f'Failed to load extension {ext}.', file=sys.stderr)
        traceback.print_exc()

# On Ready Event
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


# Catch tree errors
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    embed = discord.Embed(title="Error", description="There was an error processing the command.", color=discord.Color.red())
    embed.add_field(name= "``Error Description``", value= "*"+str(error)+"*")
    
    await interaction.response.send_message(embed= embed, ephemeral=True)

bot.tree.on_error = on_app_command_error

# Run the Bot
bot.run(token= token)
