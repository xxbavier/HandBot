from asyncio import events
import re
import time
from email import header, message
import sqlite3
from ssl import Options
from urllib import response
import discord
from discord import player, app_commands, ui
from discord.embeds import Embed
from discord.ext import commands, tasks
import psycopg2
import requests
from typing import List
import time
import threading
import datetime
import random

import json
from itertools import cycle
import math
import asyncio

import flask
from flask import Flask
import flask_restful
from flask_restful import Api, Resource, reqparse

import pymongo
from pymongo.errors import ConnectionFailure
from pymongo import InsertOne, DeleteOne, ReplaceOne

from classes import InterestForm

coachRoles = {
    'TO': 917068655928442930, # TO
    'GM': 917068674626646027, # GM
}

htl_servers = {
    "League": 909153380268650516,
    "Media": 928509118208180275,
    "Administration": 1020429868762144848
}
transactions_id = 917102767208816680
transactions_enabled = True

token: str
mongoLogIn: str

with open("config.json", "r") as file:
    data = json.load(file)
    token = data["token"]
    mongoLogIn = data["db_connection"]
    applicationId = data["application_id"]


# Initiate
mongoClient = pymongo.MongoClient(mongoLogIn)

try:
    mongoClient.admin.command("ping")
except ConnectionFailure:
    print("MongoDB server is not available.")

databases = {
    "Player Data": mongoClient["Player_Data"],
    "Contracts": mongoClient["Contracts"],
    "Demands": mongoClient["Demands"]
}


app = Flask(__name__)
api = Api(app)

bot = commands.Bot(command_prefix= "?", intents=discord.Intents.all(), application_id= applicationId)
tree = bot.tree

def coachCheck(user, htl):
    '''
    Returns coaching level of a member.
    Returns 3 if user is a Team Owner.
    Returns 2 if user is an Head Coach.
    Returns 1 if user is an Assistant Coach.
    Returns 0 if user is not a coach.
    '''

    if htl.get_role(coachRoles["TO"]) in user.roles:
        return 3
    
    elif htl.get_role(coachRoles["GM"]) in user.roles:
        return 2

    #elif htl.get_role(assistantCoach) in user.roles:
    #    return 1
    
    return 0

def teamCheck(user, htl):
    '''
    Checks to see if a player is on a valid team.
    
    Returns [True, team_role] if player is on a team.
    Returns [False, team_role] if player is not on a team.
    '''

    membership = htl.get_role(917043822402338886)
    end = htl.get_role(917043508509032508)

    onTeam = False
    teamRole = None

    for x in user.roles:
        if x.position < end.position and x.position > membership.position:
            onTeam = True
            teamRole = x
            break
        
    return [onTeam, teamRole]

def teamCheckBool(inter: discord.interactions.Interaction):
    '''
    Checks to see if a player is on a valid team.
    
    Returns [True, team_role] if player is on a team.
    Returns [False, team_role] if player is not on a team.
    '''

    membership = inter.guild.get_role(917043822402338886)
    end = inter.guild.get_role(917043508509032508)

    onTeam = False

    for x in inter.user.roles:
        if x.position < end.position and x.position > membership.position:
            onTeam = True
            break
        
    return onTeam


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

@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    embed = discord.Embed(title="Error", description="There was an error when processing the command.", color=discord.Color.red())
    embed.add_field(name= "``Error Description``", value= "*"+str(error)+"*")

    await interaction.response.send_message(embed= embed, ephemeral=True)


def isTeamRole(guild_id: str, role_id: int):
    role = bot.get_guild(guild_id).get_role(role_id)

    if role.position < bot.get_guild(guild_id).get_role(917043508509032508).position and role.position > bot.get_guild(guild_id).get_role(917043822402338886).position:
       return True
    else:
        return False


def transactionEmbed(emoji, team_role):
    embed= discord.Embed(title= "{} {}".format(emoji, team_role.name), description= "", colour= team_role.color)

    return embed

def make_players_string(list_of_players):
    string = ""

    for player in list_of_players:
        string += "{} ({})\n".format(player.mention, player.name)
    
    return string

async def teams_autocomplete(inter: discord.Integration, current: str) -> List[app_commands.Choice[str]]:
    teams = []

    for role in inter.guild.roles:
        if isTeamRole(inter.guild.id, role.id):
            teams.append([role.name, str(role.id)])
    
    choices = []

    for teamList in teams:
        choices.append(app_commands.Choice(name=teamList[0], value=teamList[1]))

    return choices


def get_members_from_string(string, htl):
    members = []

    string = string.split(" ")

    for word in string:
        if word.startswith("<@") and word.endswith(">"):
            id = ""

            for i in word:
                if i.isdigit():
                    id += str(i)

            id = int(id)
            
            if htl.get_member(id):
                members.append(htl.get_member(id))
    
    return members


@app_commands.guild_only()
class interest_sign_up(app_commands.Group, name= "interestform"):
    @app_commands.command()
    async def create(self, inter: discord.interactions.Interaction) -> None:
        await inter.response.send_modal(InterestForm())

    @app_commands.command()
    async def view(self, inter: discord.interactions.Interaction) -> None:
        pass

    @app_commands.command()
    async def edit(self, inter: discord.interactions.Interaction) -> None:
        pass

tree.add_command(interest_sign_up())

@app_commands.guild_only()
class market(app_commands.Group, name= "market", description= "Where coaches can manage their team."):
    def isCoach(member) -> list[bool, discord.Role]:
        pass

    trades = app_commands.Group(name= "trades", description= "Manage your trades.")
    
    @trades.command()
    @app_commands.checks.has_any_role("Team Owner", "General Manager")
    async def create(self, inter: discord.interactions.Interaction) -> None:
        embed = discord.Embed()

    contracts = app_commands.Group(name= "contracts", description="Manage contracts.")

    @contracts.command()
    @app_commands.checks.has_any_role("Team Owner", "General Manager")
    async def offer(self, inter: discord.interactions.Interaction, member: discord.User) -> None:
        pass

    @contracts.command()
    @app_commands.checks.has_any_role("Team Owner", "General Manager")
    async def view(self, inter: discord.interactions.Interaction) -> None:
        pass

    def canPromotePlayer(self, inter: discord.interactions.Interaction):
        valid = True

        info = teamCheck(inter.user, inter.guild)
        onTeam = info[0]
        teamRole = info[1]

        if onTeam:
            coachCount = 0

            for member in teamRole.members:
                if inter.guild.get_role(coachRoles["GM"]) in member.roles:
                    coachCount += 1

            if coachCount >= 2:
                valid = False
        
        return valid

    @app_commands.command(description="Promote a player to General Manager.")
    @app_commands.checks.has_any_role("Team Owner")
    async def promote(self, inter: discord.interactions.Interaction, member: discord.Member):
        author = inter.user
        htl = inter.guild

        team_info = teamCheck(author, htl)

        valid_team = team_info[0]
        team_role = team_info[1]

        if not valid_team:
            raise Exception("You must be a team owner on a valid team to use this command.")

        if not transactions_enabled:
            raise Exception("Transactions are closed.")

        if author == member:
            raise Exception("Attempt to use command on self.")

        if teamCheck(member, htl)[1] != team_role:
            raise Exception("Player must be on the same team as you.")

        if coachCheck(member, htl) >= 2:
            raise Exception("Player is either already at the requested coaching level or is above it. Use /demote to demote players.")
            
        if not self.canPromotePlayer(inter):
            raise Exception("You already have 2 General Managers.")
        
        for e in htl.emojis:
            if team_role.name.find(e.name) > -1:
                break
        
        embed = transactionEmbed(e, team_role)

        noti= discord.Embed(title= "You are now a General Manager for: {} {}".format(e, team_role.name), description= "", colour= team_role.color)
        noti.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)

        await member.send(
            embed= noti
        )

        await member.add_roles(htl.get_role(coachRoles["GM"]))

        embed.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)
        embed.add_field(name="``Promotion``", value= "{} ({})".format(member.mention, member.name), inline=False)

        await htl.get_channel(transactions_id).send(
            embed= embed
        )
        
        await author.send(
            content = "***You have just made a transaction.***",
            embed= embed
        )

        await inter.response.send_message(
            content= "***Check your Direct Messages with {} ({}).***".format(bot.user.mention, bot.user.name),
            ephemeral= True
        )

    @app_commands.command(description="Demote a General Manager to player.")
    @app_commands.checks.has_any_role("Team Owner")
    async def demote(self, inter: discord.interactions.Interaction, member: discord.Member):
        author = inter.user
        htl = inter.guild

        team_info = teamCheck(author, htl)

        valid_team = team_info[0]
        team_role = team_info[1]

        if not valid_team:
            raise Exception("You must be a team owner on a valid team to use this command.")

        if not transactions_enabled:
            raise Exception("Transactions are closed.")

        if author == member:
            raise Exception("Attempt to use command on self.")

        if teamCheck(member, htl)[1] != team_role:
            raise Exception("Player must be on the same team as you.")

        if coachCheck(member, htl) != 2:
            raise Exception("Player is not a General Manager.")
        
        for e in htl.emojis:
            if team_role.name.find(e.name) > -1:
                break
        
        embed = transactionEmbed(e, team_role)

        noti= discord.Embed(title= "You are no longer a General Manager for: {} {}".format(e, team_role.name), description= "", colour= team_role.color)
        noti.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)

        await member.send(
            embed= noti
        )

        await member.remove_roles(htl.get_role(coachRoles["GM"]))

        embed.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)
        embed.add_field(name="``Demotion``", value= "{} ({})".format(member.mention, member.name), inline=False)

        await htl.get_channel(transactions_id).send(
            embed= embed
        )
        
        await author.send(
            content = "***You have just made a transaction.***",
            embed= embed
        )

        await inter.response.send_message(
            content= "***Check your Direct Messages with {} ({}).***".format(bot.user.mention, bot.user.name),
            ephemeral= True
        )

    @app_commands.command(description="Demand a release from your team.")
    @app_commands.check(teamCheckBool)
    async def demand(self, inter: discord.interactions.Interaction, reason: str):
        if not transactions_enabled:
            raise Exception("Transactions are closed.")

        author = inter.user
        htl = bot.get_guild(htl_servers["League"])

        team_info = teamCheck(author, htl)
        coach_info = coachCheck(author, htl)

        tick = int(time.time())
        last_tick = None
        
        try:
            cursor = databases['Player Data']["Demands"].find_one({'_id': author.id})

            last_tick = cursor["PreviousDemand"]
        except:
            pass

        if coach_info == 3 or not team_info[0]:
            raise Exception("You must be on a valid team and not be a Team Owner to use this command.")

        if last_tick:
            if tick - last_tick <= 604800:
                raise Exception("You are on cooldown! You can demand again in around {} days.".format(round((604800 - (tick - last_tick))/86400, 2)))

        try:
            databases["Player Data"]["Demands"].insert_one({'_id': author.id, "PreviousDemand": tick})
        except:
            databases["Player Data"]["Demands"].update_one({'_id': author.id}, {'$set': {"PreviousDemand": tick}})

        await author.remove_roles(
            team_info[1],
            htl.get_role(917068674626646027) # HC
        )

        for e in htl.emojis:
            if team_info[1].name.find(e.name) > -1:
                break
        
        embed = transactionEmbed(e, team_info[1])
        embed.add_field(name= "``Demanded a Release``", value= "{} ({})".format(author.mention, author.name), inline=False)

        if reason:
            embed.add_field(name= "``Reason``", value= reason, inline=False)

        await htl.get_channel(917102767208816680).send(
            embed= embed
        )

    @app_commands.command(description="Remove players from your team's roster.")
    @app_commands.checks.has_any_role("Team Owner", "General Manager")
    async def release(self, inter: discord.interactions.Interaction, players: str):
        if not transactions_enabled:
            raise Exception("Transactions are closed.")
            
        author = inter.user
        htl = bot.get_guild(htl_servers["League"])

        coach_level = coachCheck(author, htl)
        team_info = teamCheck(author, htl)

        valid_team = team_info[0]
        team_role = team_info[1]
        
        for e in htl.emojis:
            if team_role.name.find(e.name) > -1:
                break
        
        embed = transactionEmbed(e, team_role)

        players = get_members_from_string(players, htl)

        error_players = []

        for player in players:
            if teamCheck(player, htl)[1] != team_role:
                players.remove(player)
                error_players.append(player)
                continue
            
            await player.remove_roles(team_role, htl.get_role(coachRoles["GM"]))

            noti= discord.Embed(title= "You have been released from: {} {}".format(e, team_role.name), description= "", colour= discord.Color.red())
            noti.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)

            await player.send(
                embed= noti
            )

        releasedPlayers = make_players_string(players)

        embed.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)

        if len(players) != 0: 
            embed.add_field(name="``Release``", value= releasedPlayers, inline=False)

            await htl.get_channel(transactions_id).send(
                embed= embed
            )
        
        if len(error_players) != 0:
            string_players = make_players_string(error_players)

            embed.add_field(name= "``Failed to Release``", value= string_players)

        await author.send(
            content = "***You have just made a transaction.***",
            embed= embed
        )

        await inter.response.send_message(
            content= "***Check your Direct Messages with {} ({}).***".format(bot.user.mention, bot.user.name),
            ephemeral= True
        )
    
    @app_commands.command(description="Add players to your team's roster.")
    @app_commands.checks.has_any_role("Team Owner", "General Manager")
    async def sign(self, inter: discord.interactions.Interaction, players: str):
        if not transactions_enabled:
            raise Exception("Transactions are closed")

        author = inter.user
        htl = bot.get_guild(htl_servers["League"])

        team_info = teamCheck(author, htl)

        valid_team = team_info[0]
        team_role = team_info[1]
        
        for e in htl.emojis:
            if team_role.name.find(e.name) > -1:
                break
        
        embed = transactionEmbed(e, team_role)

        players = get_members_from_string(players, htl)

        error_players = []

        for player in players:
            if teamCheck(player, htl)[0] or len(team_role.members) >= 15 or player.bot or not (inter.guild.get_role(910371139803553812) in player.roles):
                players.remove(player)
                error_players.append(player)

                continue

            await player.add_roles(team_role)

            noti= discord.Embed(title= "You have been signed to: {} {}".format(e, team_role.name), description= "If you did not give permission to this user to sign you, please create a support ticket in <#917085749030031390>.", colour= team_role.color)
            noti.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)

            await player.send(
                embed= noti
            )

        signedPlayers = make_players_string(players)

        embed.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)

        if len(players) != 0: 
            embed.add_field(name="``Sign``", value= signedPlayers, inline=False)
            embed.add_field(name="``Roster Count``", value= str(len(team_role.members)), inline=False)

            await htl.get_channel(transactions_id).send(
                embed= embed
            )
        
        if len(error_players) != 0:
            string_players = make_players_string(error_players)

            embed.add_field(name= "``Failed to Sign``", value= string_players)

        await author.send(
            content = "***You have just made a transaction.***",
            embed= embed
        )

        await inter.response.send_message(
            content= "***Check your Direct Messages with {} ({}).***".format(bot.user.mention, bot.user.name),
            ephemeral= True
        )

tree.add_command(market())

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

tree.add_command(medals())

@tree.command()
@app_commands.autocomplete(team= teams_autocomplete)
async def roster(inter: discord.Interaction, team: str, coaches: bool = False):
    team: discord.Role = inter.guild.get_role(int(team))

    for e in inter.guild.emojis:
        if team.name.find(e.name) > -1:
            break

    embed = discord.Embed(title= "{} {}".format(e, team.name), color= team.color)
    embed.set_footer(text= "Team Size: {}".format(len(team.members)))

    for member in team.members:
        if coachCheck(member, inter.guild) == 3:
            coachingPos = "``Team Owner``"
        elif coachCheck(member, inter.guild) == 2:
            coachingPos = "``General Manager``"
        else:
            if coaches:
                continue

            coachingPos = "``Player``"

        embed.add_field(name= coachingPos, value= "{} ({})".format(member.mention, member.name))

    await inter.response.send_message(embed= embed, ephemeral= True)

        

@app_commands.guild_only()
class free_agency(app_commands.Group):
    @app_commands.command()
    @app_commands.checks.has_role("Membership")
    async def post(self, inter:discord.interactions.Interaction):
        if teamCheck(inter.user, bot.get_guild(htl_servers["League"]))[0]:
            raise Exception("You are already on a team!")

        class FA_Post(ui.Modal, title= "Free Agency Post"):
            positions = ui.TextInput(label= "What positions do you play?", placeholder="Use \"\positions\" to view a list of official positions.", style=discord.TextStyle.long)
            pros = ui.TextInput(label= "What are some of your pros?", style=discord.TextStyle.long)
            cons = ui.TextInput(label= "What are some of your cons?", style= discord.TextStyle.long)
            extra = ui.TextInput(label= "Anything else you'd like to say?", style=discord.TextStyle.long)

            async def on_submit(self, interaction: discord.Interaction, /) -> None:
                post = discord.Embed(title=inter.user.name, description="A new free agency post has been made!", color= discord.Color.blurple())
                post.add_field(name= "``Positions``", value= self.positions.value, inline= False)
                post.add_field(name= "``Pros``", value= self.pros.value, inline= False)
                post.add_field(name= "``Cons``", value=self.cons.value, inline= False)
                post.add_field(name= "``Extra``", value= self.extra.value, inline= False)
                post.add_field(name= "``Contact``", value= "{} ({})".format(inter.user.mention, inter.user.name))

                await interaction.guild.get_channel(917102894522716230).send(embed= post)

                embed = discord.Embed(
                    title= "Submitted",
                    description= "Your free agency post has been successfully posted in <#917102894522716230>.",
                    color= discord.Color.green()
                )

                await interaction.response.send_message(embed=embed, ephemeral=True)

        await inter.response.send_modal(FA_Post())
        
tree.add_command(free_agency())

@app_commands.guild_only()
class moderation(app_commands.Group):
    @app_commands.command()
    @app_commands.checks.has_any_role("Founder", "President", "Director", "Executive Board", "Moderation")
    async def mute(self, inter: discord.interactions.Interaction, member: discord.Member, reason: str, minutes: int = 30, hours: int = 0, days: int = 0, weeks: int = 0):
        x = datetime.timedelta(
            minutes= minutes,
            hours= hours,
            days= days,
            weeks= weeks
        )

        await member.timeout(x)

        embed = discord.Embed(title= "Mute", color= discord.Color.red())
        embed.set_author(name= "Subject: {} ({})".format(member.name, member.id), icon_url= member.avatar.url)
        embed.add_field(name= "``Reason``", value= reason)
        embed.add_field(name= "``Length``", value= str(x))
        embed.set_footer(text= "Moderator: {} ({})".format(inter.user.name, inter.user.id), icon_url= inter.user.avatar.url)

        await inter.response.send_message(embed= embed)
        await inter.guild.get_channel(927060372127633458).send(embed= embed)
    
    @app_commands.command()
    @app_commands.checks.has_any_role("Founder", "President", "Director", "Executive Board", "Moderation")
    async def unmute(self, inter: discord.interactions.Interaction, member: discord.Member, reason: str):
        if not member.is_timed_out():
            raise Exception("Member is not muted.")

        await member.timeout(None)

        embed = discord.Embed(title= "Unmute", color= discord.Color.green())
        embed.set_author(name= "Subject: {} ({})".format(member.name, member.id), icon_url= member.avatar.url)
        embed.add_field(name= "``Reason``", value= reason)
        embed.set_footer(text= "Moderator: {} ({})".format(inter.user.name, inter.user.id), icon_url= inter.user.avatar.url)

        await inter.response.send_message(embed= embed)
        await inter.guild.get_channel(927060372127633458).send(embed= embed)

    @app_commands.command()
    @app_commands.checks.has_any_role("Founder", "President", "Director")
    async def kick(self, inter: discord.interactions.Interaction, member: discord.Member, reason: str):
        await member.kick(reason=reason)

        embed = discord.Embed(title= "Kick", color= discord.Color.red())
        embed.set_author(name= "Subject: {} ({})".format(member.name, member.id), icon_url= member.avatar.url)
        embed.add_field(name= "``Reason``", value= reason)
        embed.set_footer(text= "Moderator: {} ({})".format(inter.user.name, inter.user.id), icon_url= inter.user.avatar.url)

        await inter.response.send_message(embed= embed)
        await inter.guild.get_channel(927060372127633458).send(embed= embed)

    @app_commands.command()
    @app_commands.checks.has_any_role("Founder", "President", "Director")
    async def ban(self, inter: discord.interactions.Interaction, member: discord.Member, reason: str):
        await member.ban(reason=reason)

        embed = discord.Embed(title= "Ban", color= discord.Color.red())
        embed.set_author(name= "Subject: {} ({})".format(member.name, member.id), icon_url= member.avatar.url)
        embed.add_field(name= "``Reason``", value= reason)
        embed.set_footer(text= "Moderator: {} ({})".format(inter.user.name, inter.user.id), icon_url= inter.user.avatar.url)

        await inter.response.send_message(embed= embed)
        await inter.guild.get_channel(927060372127633458).send(embed= embed)

tree.add_command(moderation())

@tree.command()
async def positions(inter: discord.interactions.Interaction):
    embed = discord.Embed(title="Handball Positions", description="This is a list of officially recognized *Handball: The League* positions.", color=discord.Color.purple())
    embed.add_field(name= ":one: ``Striker``", value="Strikers focus on scoring the points. Strikers can usually be found on the opponent's side of the court.", inline= False)
    embed.add_field(name= ":two: ``Midfielder``", value= "Midfielders focus on moving the ball around and providing support to both defenders and strikers. Midfielders can usually be found near the middle of the court.", inline=False)
    embed.add_field(name= ":three: ``Defender``", value= "Defenders focus on stopping the opposing team's offense. Defender can usually be found on their own side of the court.", inline=False)
    embed.add_field(name= ":four: ``Goalkeeper``", value="Goalkeepers focus on saving shot attempts made by the opposing team. Goalkeepers can usually be found inside of the smaller ring circling the goal. A team can only have 1 GK at time.", inline=False)

    await inter.response.send_message(embed= embed, ephemeral= True)

@tree.command()
async def submit_scores(inter: discord.interactions.Interaction, week: discord.Attachment):
    class ReportScores(ui.Modal, title= "Submit Game Scores"):
        def __init__(self, *, title: str = ..., wk: int) -> None:
            super().__init__(title=title)
            self["week"] = wk
        
        team_one = ui.TextInput(label= 'Please name Team 1.', style= discord.TextStyle.short)
        team_one_score = ui.TextInput(label= 'What was the score for Team 1?', style= discord.TextStyle.short, placeholder="This MUST be a number.", max_length= 3)
        team_two = ui.TextInput(label= 'Please name Team 2.', style= discord.TextStyle.short)
        team_two_score = ui.TextInput(label= 'What was the score for Team 2?', style= discord.TextStyle.short, placeholder="This MUST be a number.", max_length= 3)

        async def on_submit(self, inter: discord.interactions.Interaction):
            scores = {
                'team_one': int(self.team_one_score.value),
                'team_two': int(self.team_two_score.value)
            }

            embed = discord.Embed(title= "WEEK {} | {} vs {}".format(getattr(self, 'week'), self.team_one.value, self.team_two.value))
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

            embed = discord.Embed(title= "Game Scores Submitted!", description= "Here's a receipt of what you submitted:")
            embed.add_field(name= "``Week``", value= getattr(self, 'week'), inline=False)
            embed.add_field(name= "``Team 1 Name``", value= self.team_one.value, inline=False)
            embed.add_field(name= "``Team 1 Score``", value= self.team_one_score.value, inline=False)
            embed.add_field(name= "``Team 2 Name``", value= self.team_two.value, inline=False)
            embed.add_field(name= "``Team 2 Score``", value= self.team_two_score.value, inline=False)

            await inter.response.send_message(embed= embed, ephemeral=True)
    
    await inter.response.send_modal(ReportScores())

@tree.command()
async def apply(inter: discord.Interaction):
    pass

@tree.command()
async def verify(inter: discord.interactions.Interaction):
    isPlayerVerified = databases["Player Data"]["Verification"].find_one({
        'discord': inter.user.name
    })

    if isPlayerVerified:
        if isPlayerVerified["confirmed"]:
            await inter.user.add_roles(910371139803553812)
            raise Exception("You are already verified!")

    await inter.response.send_message(content="***Check your DMs with {}!***".format(bot.user.mention), ephemeral= True)

    embed = discord.Embed(title= "HTL Verification", description="Welcome to the HTL verification system! Once you finish this, you will have full access to HTL.")
    embed.add_field(name="``Get Started``", value= "Click \"Start\" below to begin.")

    class stepOne(ui.View):
        @ui.button(label='Start', style= discord.ButtonStyle.green)
        async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
            class modal(ui.Modal, title= "Verification | Step One"):
                robloxUsername = ui.TextInput(label="What is your Roblox username?")

                async def on_submit(self, interaction: discord.interactions.Interaction):
                    robloxUsername = self.robloxUsername.value
                    response = requests.request("GET", 'https://users.roblox.com/v1/users/search?keyword={}&limit=10'.format(robloxUsername), headers={'content-type': 'application/json; charset=utf-8', 'X-Requested-With': 'XMLHttpRequest'})
                    data = json.loads(response.content)
                    data = data["data"]
                    account = data[0]

                    confirm = discord.Embed(title= "Is this you?")
                    confirm.add_field(name= "``Username``", value= account["name"])
                    confirm.add_field(name= "``UserId``", value= account["id"])
                    confirm.set_thumbnail(url= "https://www.roblox.com/headshot-thumbnail/image?userId={}&width=420&height=420&format=png".format(account["id"]))

                    class confirmView(ui.View):
                        @ui.button(label= "Yes", style=discord.ButtonStyle.green)
                        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                            def checkGroup():
                                isInGroup = requests.request('GET', "https://groups.roblox.com/v2/users/{}/groups/roles".format(account["id"]), headers={'content-type': 'application/json; charset=utf-8', 'X-Requested-With': 'XMLHttpRequest'})
                                isInGroup = json.loads(isInGroup.content)

                                for group in isInGroup["data"]:
                                    if group["group"]["id"] == 10195697:
                                        return True

                                return False

                            if not checkGroup():
                                await interaction.response.send_message("*It appears that you are not in the HTL group.\nJoin this group and then try again: {}*".format("https://www.roblox.com/groups/10195697/Handball-The-League#!/about"), ephemeral=True)
                            else:
                                await interaction.message.delete()
                                try:
                                    databases["Player Data"]["Verification"].update_one({'discord': inter.user.id}, {'$set': {'roblox': account["id"], 'confirmed': False}}, upsert=True)
                                except:
                                    await interaction.response.send_message(content="*There was an error during saving your information. Please restart using the ``/verify`` command.")
                                    return
                            
                                await interaction.response.send_message(content="**Your information has been saved, you are almost done!\n\nAll you have to do is join the following game and click \"Verify\"\nhttps://www.roblox.com/games/6732385646/Handball-The-Hub.**")
                            
                        @ui.button(label= "No", style= discord.ButtonStyle.red)
                        async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
                            await interaction.response.send_message(content="*Please restart by using the ``/verify`` command.*")

                    await msg.delete()
                    await interaction.response.send_message(embed= confirm, view= confirmView())


            await interaction.response.send_modal(modal())

    msg = await inter.user.send(embed=embed, view=stepOne())
    


@api.resource("/verify")
class Verify(Resource):
    def get(self):
        reqparser = reqparse.RequestParser()

        reqparser.add_argument("platform", required= True)
        reqparser.add_argument("id", required= True)

        args = reqparser.parse_args()

        data = databases["Player Data"]["Verification"].find_one({
            args["platform"]: args["id"]
        })

        if data:
            ids = {}

            try:
                ids["discord"] = data["discord"]
            except:
                ids["discord"] = None
            
            try:
                ids["roblox"] = data["roblox"]
            except:
                ids["roblox"] = None

            try:
                ids["confirmed"] = data["confirmed"]
            except:
                ids["confirmed"] = False

            return {
                'discord': ids["discord"],
                'roblox': ids["roblox"],
                'confirmed': ids["confirmed"]
            }

        return None

    def post(self):
        reqparser = reqparse.RequestParser()

        reqparser.add_argument("platform", required= True)
        reqparser.add_argument("id", required= True)

        args = reqparser.parse_args()

        data = databases["Player Data"]["Verification"].find_one({
            args["platform"]: args["id"]
        })

        if data:
            databases["Player Data"]["Verification"].update_one({'discord': data["discord"], 'roblox': data["roblox"]}, {'$set': {'confirmed': True}})

            member = bot.get_guild(htl_servers["League"]).get_member(data["discord"])
            embed = discord.Embed(title= member.name, color= discord.Color.green())
            embed.add_field(name="``Member Mention``", value= member.mention, inline= True)
            embed.add_field(name="``Member ID``", value= member.id, inline= True)

            asyncio.run(bot.get_guild(htl_servers["League"]).get_channel(1070807124537507850).send(embed=embed))

            return {"Success": "Your account has been confirmed!"}

        return {"Error": "No data found for this user. Begin verification process in HTL."}


discordBot = threading.Thread(target=bot.run, kwargs=({'token': token}))
apiServer = threading.Thread(target=app.run, kwargs={'host': '0.0.0.0'})
discordBot.start()
apiServer.start()

discordBot.join()
apiServer.join()