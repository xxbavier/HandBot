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
from Commands import admin, league, moderation
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
roClient = roblox.Client()
tree = bot.tree

def get_roles(member: discord.Member, adding_roles: bool):
    roles = [
        ["🤾", "Pickup Pings", 917051613196193812],
        ["🎮", "Event Pings", 917051775754829874],
        ["📺", "Stream Pings", 1088688412850135112],
        ["🚫", "Mute Partnerships", 917051682343501884],
        ["🔰", "Team Owner Interest", 944096262779719681],
        ["🔨", "Handball Development", 1096528717557284944]
    ]

    approved_role_choices = []

    for role in roles:
        role_obj = member.guild.get_role(role[2])

        if role_obj and ((role_obj in member.roles) != adding_roles):
            option = discord.SelectOption(label= role[1], value= role[2], emoji= role[0])

            approved_role_choices.append(option)

    return approved_role_choices

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

msgLength = random.randint(1,100)
randomMsg = []

@bot.event
async def on_message(msg: discord.Message):
    '''if msg.channel == msg.guild.get_channel(917049598059618405):
        global randomMsg
        global msgLength

        word = random.choice(msg.content.split(" "))
        randomMsg.append(word)

        if len(randomMsg) >= msgLength:
            message = " ".join(randomMsg)
            message = message.lower().capitalize()
            randomMsg = []
            await msg.guild.get_channel(917049598059618405).send(content=message)
            msgLength = random.randint(1,100)'''

    if(msg.channel.id == 917103851092476074):
        if (msg.content.startswith('<:htl_twitter:951619979252482088>')):
            if teamCheck(msg.author, msg.guild)[1]:
                await msg.add_reaction('<:htl_verified:951652612120395846>')
      
            await msg.add_reaction('❤️')
            await msg.add_reaction('<:htl_retweet:951620081488642068>')
      
        else:
            try:
                await msg.delete()
            except Exception:
                pass
        await bot.process_commands(msg)

@bot.event
async def on_member_join(member: discord.Member):
    roles = [
        1209253356829151272,
        1192374103609454683,
        1192374441934602340,
        1189126244743262278,
        1241443258500907139,
        1192373637173477437
    ]

    await member.add_roles(*[bot.get_guild(htl_servers["League"]).get_role(role) for role in roles])
    await member.guild.get_channel(1189275682639990924).send(content="<:Green:1209279977883836467> | **{} has joined the server.** ``Members: {}``".format(member.mention, member.guild.member_count))

@bot.event
async def on_raw_member_remove(member: discord.RawMemberRemoveEvent):
    await bot.get_guild(member.guild_id).get_channel(1189275682639990924).send(content="<:Red:1209279976524877884> | *{}#{} has left the server.*".format(member.user.name, member.user.discriminator))

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    hasRole = False

    for role in after.roles:
        if role.id == 910372383808958486:
            hasRole = True
            break

    if not hasRole:
        above = 0
        below = 0
        roles_to_remove = []

        for role in after.guild.roles:
            if role.name == "----- COLORS BELOW -----":
                above = role.position
                continue
            elif role.name == "----- COLORS ABOVE -----":
                below = role.position
                continue

        for role in after.roles:
            if role.position >= below and role.position < above:
                roles_to_remove.append(role)
        
        if roles_to_remove != []:
            print("removing colors from "+ after.name)
            try:
                await after.remove_roles(*roles_to_remove, reason= "User is no longer boosting; therefore, I am taking away the color roles.")
            except Exception as e:
                print("Failed to remove color from "+ after.name)
    
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    embed = discord.Embed(title="Error", description="There was an error when processing the command.", color=discord.Color.red())
    embed.add_field(name= "``Error Description``", value= "*"+str(error)+"*")

    await interaction.response.send_message(embed= embed, ephemeral=True)

tree.on_error = on_app_command_error

bot.run(token= token)