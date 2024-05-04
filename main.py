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
from Commands import moderation,admin,market
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
    await member.guild.get_channel(1073647165613809715).send(content="<:htlg:1073648808845647912> | **{} has joined the server.** ``Members: {}``".format(member.mention, member.guild.member_count))

@bot.event
async def on_raw_member_remove(member: discord.RawMemberRemoveEvent):
    await bot.get_guild(member.guild_id).get_channel(1073647165613809715).send(content="<:htlr:1073648809873260707> | *{}#{} has left the server.*".format(member.user.name, member.user.discriminator))

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
    
#tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    embed = discord.Embed(title="Error", description="There was an error when processing the command.", color=discord.Color.red())
    embed.add_field(name= "``Error Description``", value= "*"+str(error)+"*")

    await interaction.response.send_message(embed= embed, ephemeral=True)

#@tree.command()
@app_commands.checks.has_any_role("Team Owner", "General Manager", "Referees", "Streamers")
async def game_results(inter: discord.interactions.Interaction, stats_video: str = None, stats_file1: discord.Attachment = None, stats_file2: discord.Attachment = None, stats_file3: discord.Attachment = None, stats_file4: discord.Attachment = None, stats_file5: discord.Attachment = None, stats_file6: discord.Attachment = None, stats_file7: discord.Attachment = None):
    files = []
    
    class ReportScores(ui.Modal, title= "Submit Game Scores"):
        week = ui.TextInput(label= "What week is this game from?", style= discord.TextStyle.short, placeholder="This MUST be a number.", max_length= 2)
        team_one = ui.TextInput(label= 'Please name Team 1.', style= discord.TextStyle.short)
        team_one_score = ui.TextInput(label= 'What was the score for Team 1?', style= discord.TextStyle.short, placeholder="This MUST be a number.", max_length= 3)
        team_two = ui.TextInput(label= 'Please name Team 2.', style= discord.TextStyle.short)
        team_two_score = ui.TextInput(label= 'What was the score for Team 2?', style= discord.TextStyle.short, placeholder="This MUST be a number.", max_length= 3)

        async def on_submit(self, inter: discord.interactions.Interaction):
            int(self.week.value)
            int(self.team_one_score.value)
            int(self.team_two_score.value)

            scores = {
                'team_one': int(self.team_one_score.value),
                'team_two': int(self.team_two_score.value)
            }

            embed = discord.Embed(title= "WEEK {} | {} vs {}".format(self.week.value, self.team_one.value, self.team_two.value))
            embed.add_field(name= "``{} Score``".format(self.team_one.value), value= scores['team_one'], inline=False)
            embed.add_field(name= "``{} Score``".format(self.team_two.value), value= scores['team_two'], inline=False)

            if scores["team_one"] > scores["team_two"]:
                winner = {
                    'Name': self.team_one.value,
                    'Score': scores["team_one"]
                }

                loser = {
                    'Name': self.team_two.value,
                    'Score': scores["team_two"]
                }
            else:
                winner = {
                    'Name': self.team_two.value,
                    'Score': scores["team_two"]
                }

                loser = {
                    'Name': self.team_one.value,
                    'Score': scores["team_one"]
                }
            
            embed.add_field(name="``Result``", value='{} beats {}. Score was {} - {}.'.format(winner["Name"], loser["Name"], winner["Score"], loser["Score"]), inline=False)

            embed.set_footer(text= "Submitted by {}".format(inter.user.name), icon_url=inter.user.avatar.url)

            await inter.guild.get_channel(1068918752776818779).send(embed=embed)
            await inter.guild.get_channel(1073662090113450014).send(content= "``Week {}``\n**> {} vs {}**\n> Stats video: {}".format(self.week.value, self.team_one.value, self.team_two.value, stats_video or "No video provided"), files= files)

            embed = discord.Embed(title= "Game Scores Submitted!", description= "Here's a receipt of what you submitted:")
            embed.add_field(name= "``Week``", value= self.week.value, inline=False)
            embed.add_field(name= "``Team 1 Name``", value= self.team_one.value, inline=False)
            embed.add_field(name= "``Team 1 Score``", value= self.team_one_score.value, inline=False)
            embed.add_field(name= "``Team 2 Name``", value= self.team_two.value, inline=False)
            embed.add_field(name= "``Team 2 Score``", value= self.team_two_score.value, inline=False)

            await inter.response.send_message(embed= embed, ephemeral=True)

    for file in [stats_file1, stats_file2, stats_file3, stats_file4, stats_file5, stats_file6, stats_file7]:
        if file:
            files.append(await file.to_file())

    await inter.response.send_modal(ReportScores())

bot.run(token= token)