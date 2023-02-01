from asyncio import events
import re
import time
from email import header, message
import sqlite3
from ssl import Options
from urllib import response
import discord
from discord import player, app_commands
from discord.embeds import Embed
from discord.ext import commands, tasks
import psycopg2
import requests
from typing import List
import time

import keep_alive
import json
from itertools import cycle
import math
import asyncio

import pymongo
from pymongo.errors import ConnectionFailure
from pymongo import InsertOne, DeleteOne, ReplaceOne

from classes import InterestForm, ReportScores

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

    syncedcommands = await bot.tree.sync()
    await bot.change_presence(status= discord.Status.online, activity= discord.Game("Handball"))

    commands_list = ""
    for cmd in syncedcommands:
        commands_list += "\n    - " + cmd.name

    print("Logged into {} and fully functional with the following commands: {}".format(bot.user.name, commands_list))

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

@tree.command()
async def medals(inter: discord.interactions.Interaction, member: discord.User):
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

@tree.command()
async def positions(inter: discord.interactions.Interaction):
    embed = discord.Embed(title="Handball Positions", description="This is a list of officially recognized *Handball: The League* positions.", color=discord.Color.purple())
    embed.add_field(name= ":one: ``Striker``", value="Strikers focus on scoring the points. Strikers can usually be found on the opponent's side of the court.", inline= False)
    embed.add_field(name= ":two: ``Midfielder``", value= "Midfielders focus on moving the ball around and providing support to both defenders and strikers. Midfielders can usually be found near the middle of the court.", inline=False)
    embed.add_field(name= ":three: ``Defender``", value= "Defenders focus on stopping the opposing team's offense. Defender can usually be found on their own side of the court.", inline=False)
    embed.add_field(name= ":four: ``Goalkeeper``", value="Goalkeepers focus on saving shot attempts made by the opposing team. Goalkeepers can usually be found inside of the smaller ring circling the goal. A team can only have 1 GK at time.", inline=False)

    await inter.response.send_message(embed= embed, ephemeral= True)

@tree.command()
async def submit_scores(inter: discord.interactions.Interaction, week: int):
    modal = ReportScores(wk= week)
    
    await inter.response.send_modal(modal)

bot.run(token=token)