import os
import re
import time
from dis import disco
from email import message
from pydoc import describe
import sqlite3
from ssl import Options
from urllib import response
import discord
from discord import player
from discord.embeds import Embed
from discord.ext import commands, tasks
from discord.utils import parse_time
from dislash import InteractionClient, ActionRow, Button, ButtonStyle, SelectMenu, SelectOption, ContextMenuInteraction, Option, OptionType
from dislash.interactions.message_components import Component
import psycopg2
from colorthief import ColorThief

import keep_alive
import json
from itertools import cycle
import math

# Initiate
keep_alive.keep_alive()
intents = discord.Intents().all()

with open('config.json') as f:
  config = json.load(f)
token = config.get('token')

bot = commands.Bot(command_prefix=("?"), intents= intents)
int_bot = InteractionClient(bot, test_guilds=[823037558027321374, 909153380268650516], modify_send= True)

status = cycle(['Handball','Xavs Simulator'])

transactions_enabled = True

next_season_identifier = "S3"
playoffs = True

transactions_id = 917102767208816680

teamOwner = 917068655928442930
headCoach = 917068674626646027
assistantCoach = 917068697334595664

demands = {
    2: 942302221696135198,
    1: 942302278054985808,
    0: 942302302037999616
}

htl_servers = {
    "League": 909153380268650516,
    "Media": 928509118208180275
}

def rgb_to_hex(rgb):
    return '%02x%02x%02x' % rgb

def team_role_check(role):
    htl = bot.get_guild(htl_servers["League"])

    membership = htl.get_role(917043822402338886)
    end = htl.get_role(917043508509032508)

    if role.position < end.position and role.position > membership.position:
        return True
    return False

def find_emojis(msg):
    custom_emojis = re.findall(r'<:\w*:\d*>', msg)
    custom_emojis = [int(e.split(':')[2].replace('>', '')) for e in custom_emojis]
    custom_emojis = [discord.utils.get(bot.emojis, id=e) for e in custom_emojis]

    return custom_emojis

def coachCheck(user, htl):
    '''
    Returns coaching level of a member.

    Returns 3 if user is a Team Owner.
    Returns 2 if user is an Head Coach.
    Returns 1 if user is an Assistant Coach.
    Returns 0 if user is not a coach.
    '''

    if htl.get_role(teamOwner) in user.roles:
        return 3
    
    elif htl.get_role(headCoach) in user.roles:
        return 2

    elif htl.get_role(assistantCoach) in user.roles:
        return 1
    
    return 0

def next_season_team_check(team):
    if team.name.find(next_season_identifier) >= 0:
        return True
    
    return False

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
        else:
            onTeam = False
        
    return [onTeam, teamRole]


def error(command, reason):
    embed = discord.Embed(title="{} Error".format(command), description= "There was an error while executing this command.", colour= discord.Colour.red())
    embed.add_field(name="``Reason``", value=reason)

    return embed

@int_bot.event
async def on_ready():
  change_status.start()
  print("Your bot is ready")


@tasks.loop(seconds=30)
async def change_status():
  #await bot.wait_until_ready()
  #general = bot.get_channel(891224542603800638)
  await bot.change_presence(activity=discord.Game(next(status)))
  #await general.send(content="Who else high af rn")


# Main
"""
with open('stuff.json', "r") as f:
    config = json.loads(f.read())
token = config.get('token')
"""

@bot.event
async def on_message(msg):
  if(msg.channel.id == 917103851092476074):
    if (msg.content.startswith('<:htl_twitter:951619979252482088>')):
      if teamCheck(msg.author, msg.guild):
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
async def on_member_remove(member):
    htl = bot.get_guild(909153380268650516)

    for demand in demands.values():
        role = htl.get_role(demand)

        if role in member.roles:
            embed = discord.Embed(title= "Member With Demands Has Left the Server.", description= "", colour= discord.Color.red())

            embed.add_field(name="``Demands``", value=role.mention)

            embed.set_footer(text= member.name + "#" + member.discriminator, icon_url= member.avatar_url)

            await htl.get_channel(943324167154053250).send(embed= embed)

            break


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


@int_bot.slash_command(
    description= "Sign player(s) to the team you are roled to. Must be a Assistant Coach+.",
    options=[
        Option("players", "Please mention (ping) all of players you're signing here.", OptionType.STRING, required= True)
    ]
)
async def sign(inter, players= None):
    if not transactions_enabled:
        embed = error("sign", "Transactions are closed.")

        await inter.create_response(
            embed= embed,
            ephemeral= True
        )

        return

    author = inter.author
    htl = bot.get_guild(htl_servers["League"])

    coach_level = coachCheck(author, htl)
    team_info = teamCheck(author, htl)

    valid_team = team_info[0]
    team_role = team_info[1]

    if playoffs:
        valid_team = next_season_team_check(team_role)
    
    if coach_level == 0 or not valid_team:
        await inter.create_response(
            embed= error("release", "You must be a coach on a valid team to use this command."),
            ephemeral= True
        )
        return
    
    for e in htl.emojis:
        if team_role.name.find(e.name) > -1:
            break
    
    embed = transactionEmbed(e, team_role)

    players = get_members_from_string(players, htl)

    error_players = []

    for player in players:
        if teamCheck(player, htl)[0] or len(team_role.members) >= 15 or player.bot:
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

    await inter.create_response(
        content= "***Check your Direct Messages with {} ({}).***".format(bot.user.mention, bot.user.name),
        ephemeral= True
    )


@int_bot.slash_command(
    description= "Suggest ideas to be considered for the league.",
    options=[
        Option("suggestion", "What is your suggestion?", OptionType.STRING, required= True)
    ]
)
async def suggest(inter, suggestion= None):
    author = inter.author
    htl = bot.get_guild(htl_servers["League"])

    await inter.create_response(
        embed = discord.Embed(title= "Your suggestion has been recorded.".format(author.name + "#" + author.discriminator), description= suggestion, colour= discord.Color.green()),
        ephemeral= True
    )

    embed= discord.Embed(title= "Suggestion | {}".format(author.name + "#" + author.discriminator), description= suggestion, colour= discord.Color.blurple())
    embed.set_footer(text= author.name + "#" + author.discriminator, icon_url= author.avatar_url)

    msg = await htl.get_channel(941826291550793838).send(
        embed= embed
    )

    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

def get_demands(user, htl):
    dr = 3

    for demands_remaining, role_id in demands.items():
        if htl.get_role(role_id) in user.roles:
            dr = demands_remaining
            break
    
    return dr

@int_bot.slash_command(
    description= "Demand a release from a team.",
    options=[
        Option("reason", "Is there any reason for why you're demanding a release?", OptionType.STRING, required= False)
    ]
)
async def demand(inter, reason= None):
    if not transactions_enabled:
        embed = error("demand", "Transactions are closed.")

        await inter.create_response(
            embed= embed,
            ephemeral= True
        )

        return

    author = inter.author
    htl = bot.get_guild(htl_servers["League"])

    team_info = teamCheck(author, htl)

    valid_team = team_info[0]
    team_role = team_info[1]

    coach_info = coachCheck(author, htl)
    demands_info = get_demands(author, htl)

    if playoffs:
        valid_team = next_season_team_check(team_role)

    if coach_info == 3 or not valid_team:
        await inter.create_response(
            embed= error("demand", "You must be on a valid team and not be a Team Owner to use this command."),
            ephemeral= True
        )
        return

    if demands_info == 0:
        await inter.create_response(
            embed= error("demand", "You do not have any more demands available."),
            ephemeral= True
        )
        return

    if demands_info == 3:
        await author.remove_roles(htl.get_role(demands[1]), htl.get_role(demands[0]))
        await author.add_roles(htl.get_role(demands[2]))
    elif demands_info == 2:
        await author.remove_roles(htl.get_role(demands[2]), htl.get_role(demands[0]))
        await author.add_roles(htl.get_role(demands[1]))
    elif demands_info:
        await author.remove_roles(htl.get_role(demands[2]), htl.get_role(demands[1]))
        await author.add_roles(htl.get_role(demands[0]))

    await author.remove_roles(
        team_info[1],
        htl.get_role(917068697334595664), # AC
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



@int_bot.slash_command(
    description= "Release player(s) from the team you are roled to. Must be a Assistant Coach+.",
    options=[
        Option("players", "Please mention (ping) all of players you're releasing here.", OptionType.STRING, required= True)
    ]
)
async def release(inter, players= None):
    if not transactions_enabled:
        embed = error("release", "Transactions are closed.")

        await inter.create_response(
            embed= embed,
            ephemeral= True
        )

        return
        
    author = inter.author
    htl = bot.get_guild(htl_servers["League"])

    coach_level = coachCheck(author, htl)
    team_info = teamCheck(author, htl)

    valid_team = team_info[0]
    team_role = team_info[1]

    if playoffs:
        valid_team = next_season_team_check(team_role)
    
    if coach_level == 0 or not valid_team:
        await inter.create_response(
            embed= error("release", "You must be a coach on a valid team to use this command."),
            ephemeral= True
        )
        return
    
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
        
        await player.remove_roles(team_role)

        noti= discord.Embed(title= "You have been released from: {} {}".format(e, team_role.name), description= "", colour= discord.Color.red())
        noti.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)

        await player.send(
            embed= noti
        )

    signedPlayers = make_players_string(players)

    embed.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)

    if len(players) != 0: 
        embed.add_field(name="``Release``", value= signedPlayers, inline=False)

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

    await inter.create_response(
        content= "***Check your Direct Messages with {} ({}).***".format(bot.user.mention, bot.user.name),
        ephemeral= True
    )


@int_bot.slash_command(
    description= "Promote players to a coaching position. Must be a Team Owner.",
    options=[
        Option("player", "Please mention (ping) the player you're promoting here.", OptionType.USER, required= True),
        Option("coach", "Please state the level of coaching. 1 = Assistant Coach, 2 = Head Coach.", OptionType.INTEGER, required= True)
    ]
)
async def promote(inter, player= None, coach= None):
    if not transactions_enabled:
        embed = error("promote", "Transactions are closed.")

        await inter.create_response(
            embed= embed,
            ephemeral= True
        )

        return
    author = inter.author
    htl = bot.get_guild(htl_servers["League"])

    if author == player:
        await inter.create_response(
            embed= error("promote", "Attempt to use command on self."),
            ephemeral= True
        )

    if coach != 1 and coach != 2:
        embed = error("promote", "Invalid coach level. If you attempted to transfer Team Owner, you must submit a ticket in <#917085749030031390> to request this.")

        await inter.create_response(
            embed= embed,
            ephemeral= True
        )

        return
    else:
        if coach == 1:
            coachingRole = assistantCoach
            coachPos = "Assistant Coach"
        else:
            coachingRole = headCoach
            coachPos = "Head Coach"
    
    if coach <= coachCheck(player, htl):
        embed = error("promote", "Player is either already at the requested coaching level or is above it. Use /demote to demote players.")

        await inter.create_response(
            embed= embed,
            ephemeral= True
        )

        return
    
    if not transactions_enabled:
        embed = error("promote", "Transactions are closed.")

        await inter.create_response(
            embed= embed,
            ephemeral= True
        )

        return
        
    coach_level = coachCheck(author, htl)
    team_info = teamCheck(author, htl)

    valid_team = team_info[0]
    team_role = team_info[1]
    
    if coach_level != 3 and not valid_team:
        await inter.create_response(
            embed= error("promote", "You must be a coach on a valid team to use this command."),
            ephemeral= True
        )
        return
    
    for e in htl.emojis:
        if team_role.name.find(e.name) > -1:
            break
    
    embed = transactionEmbed(e, team_role)

    if teamCheck(player, htl)[1] != team_role:
        await inter.create_response(
            embed= error("promote", "Player must be on the same team as you."),
            ephemeral= True
        )
        return

    noti= discord.Embed(title= "You have been demoted to {} for: {} {}".format(coachPos, e, team_role.name), description= "", colour= discord.Color.red())
    noti.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)

    await player.send(
        embed= noti
    )

    await player.remove_roles(htl.get_role(assistantCoach), htl.get_role(headCoach))
    await player.add_roles(htl.get_role(coachingRole))

    embed.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)
    embed.add_field(name="``Promotion``", value= "{} ({})".format(player.mention, player.name), inline=False)

    await htl.get_channel(transactions_id).send(
        embed= embed
    )
    
    await author.send(
        content = "***You have just made a transaction.***",
        embed= embed
    )

    await inter.create_response(
        content= "***Check your Direct Messages with {} ({}).***".format(bot.user.mention, bot.user.name),
        ephemeral= True
    )

@int_bot.slash_command(
    description= "Demote players to a coaching position or regular player. Must be a Team Owner.",
    options=[
        Option("player", "Please mention (ping) the player you're promoting here.", OptionType.USER, required= True),
        Option("coach", "Please state the level of coaching. 0 = Player, 1 = Assistant Coach.", OptionType.INTEGER, required= True)
    ]
)
async def demote(inter, player= None, coach= None):
    if not transactions_enabled:
        embed = error("demote", "Transactions are closed.")

        await inter.create_response(
            embed= embed,
            ephemeral= True
        )

        return
    author = inter.author
    htl = bot.get_guild(htl_servers["League"])

    if coach != 0 and coach != 1:
        embed = error("demote", "Invalid coach level. If you attempted to transfer Team Owner, you must submit a ticket in <#917085749030031390> to request this.")

        await inter.create_response(
            embed= embed,
            ephemeral= True
        )

        return
    else:
        if coach == 0:
            coachingRole = 0
            coachPos = "Player"
        else:
            coachingRole = assistantCoach
            coachPos = "Assistant Coach"
    
    if coach >= coachCheck(player, htl):
        embed = error("demote", "Player is either already at the requested coaching level or is below it. Use /promote to promote players.")

        await inter.create_response(
            embed= embed,
            ephemeral= True
        )

        return
    
    if not transactions_enabled:
        embed = error("demote", "Transactions are closed.")

        await inter.create_response(
            embed= embed,
            ephemeral= True
        )

        return
        
    coach_level = coachCheck(author, htl)
    team_info = teamCheck(author, htl)

    valid_team = team_info[0]
    team_role = team_info[1]
    
    if coach_level != 3 and not valid_team:
        await inter.create_response(
            embed= error("demote", "You must be a coach on a valid team to use this command."),
            ephemeral= True
        )
        return
    
    for e in htl.emojis:
        if team_role.name.find(e.name) > -1:
            break
    
    embed = transactionEmbed(e, team_role)

    if teamCheck(player, htl)[1] != team_role:
        await inter.create_response(
            embed= error("demote", "Player must be on the same team as you."),
            ephemeral= True
        )
        return

    noti= discord.Embed(title= "You have been demoted to {} for: {} {}".format(coachPos, e, team_role.name), description= "", colour= discord.Color.green())
    noti.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)

    await player.send(
        embed= noti
    )

    await player.remove_roles(htl.get_role(assistantCoach), htl.get_role(headCoach))

    if coachingRole != 0:
        await player.add_roles(htl.get_role(coachingRole))

    embed.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)
    embed.add_field(name="``Demotion``", value= "{} ({})".format(player.mention, player.name), inline=False)

    await htl.get_channel(transactions_id).send(
        embed= embed
    )
    
    await author.send(
        content = "***You have just made a transaction.***",
        embed= embed
    )

    await inter.create_response(
        content= "***Check your Direct Messages with {} ({}).***".format(bot.user.mention, bot.user.name),
        ephemeral= True
    )

'''
@int_bot.slash_command(
    description= "Release player(s) from the team you are roled to. Must be a Assistant Coach+.",
    options=[
        Option("players", "Please mention (ping) all of players you're releasing here.", OptionType.STRING, required= True)
    ]
)
async def trade(inter, players= None):
    if not transactions_enabled:
        embed = error("sign", "Transactions are closed.")

        await inter.create_response(
            embed= embed,
            ephemeral= True
        )

        return

    author = inter.author

    coach_level = coachCheck(author, htl)
    team_info = teamCheck(author, htl)

    if coach_level == 0 or not valid_team:
        await inter.create_response(
            embed= error("release", "You must be a coach on a valid team to use this command."),
            ephemeral= True
        )
        return
'''

#@int_bot.slash_command()
async def changething(ctx):
    channels = ctx.guild.channels

    for channel in channels:
        if channel.name.find("》"):
            print("Found symbol")
            oldname = channel.name
            newname = oldname.replace("》", "┃")
            await channel.edit(name=newname)
        else:
            print("Didnt find symbol")

@int_bot.slash_command()
async def post(ctx):
    author = ctx.author
    guild = ctx.guild

    membership = guild.get_role(917043822402338886)
    end = guild.get_role(917043508509032508)

    fa = True

    for r in guild.roles:
        if r in author.roles:
            if r.position < end.position and r.position > membership.position:
                fa = False

    free_agency = guild.get_channel(917102894522716230)

    embed = discord.Embed(title="Check your DMs!", description= "Check your DMs and answer thew questions asked.", colour= discord.Colour.blue())

    if fa:
        await ctx.create_response(
            embed= embed,
            ephemeral = True
        )
    if not fa:
        embed.title = "You must be a Free Agent to use this command."
        embed.description = ""

        await ctx.create_response(
            embed= embed,
            ephemeral = True
        )

        return

    embed = discord.Embed(title="Free Agency Post", colour= discord.Colour.blue())

    msg = await author.send(
        content= "***What positions do you play?***",
        embed= embed
    )

    def check(m):
        return m.author == author and m.channel == msg.channel

    m = await bot.wait_for('message', check=check, timeout=180.0)
    
    embed.add_field(name= "``Positions``", value= m.content, inline= False)

    await author.send(
        content= "***What are your pros?***",
        embed= embed
    )

    m = await bot.wait_for('message', check=check, timeout=180.0)

    embed.add_field(name= "``Pros``", value= m.content, inline= False)

    await author.send(
        content= "***What are your cons?***",
        embed= embed
    )

    m = await bot.wait_for('message', check=check, timeout=180.0)

    embed.add_field(name= "``Cons``", value= m.content, inline= False)

    await author.send(
        content= "***Is there anything else you'd like to say?***",
        embed= embed
    )

    m = await bot.wait_for('message', check=check, timeout=180.0)

    embed.add_field(name= "``Extra``", value= m.content, inline= False)

    msg = await author.send(
        content= "***Does everything here look ok?***",
        embed= embed
    )

    await msg.add_reaction('✅')
    await msg.add_reaction('❌')

    def check(reaction, user):
        return user == author and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')

    reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)

    if str(reaction.emoji) == '✅':
        await author.send(
            content= "***Posting...***"
        )

        embed.add_field(name= "``Contact``", value= author.mention)

        await free_agency.send(
            embed= embed
        )
    elif str(reaction.emoji) == '❌':
        await author.send(
            content= "***Cancelled...***"
        )

        return

@int_bot.slash_command(description= "Submit your game time.")
async def gametime(inter):
    def check(user):
        to = inter.guild.get_role(917068655928442930)
        hc = inter.guild.get_role(917068674626646027)
        ac = inter.guild.get_role(917068697334595664)

        if to in user.roles or hc in user.roles or ac in user.roles:
            return True
        else:
            return False

    author = inter.author

    if check(author):
        guild = await bot.fetch_guild(909153380268650516)

        channel = guild.get_channel(917109847709859920)

        membership = guild.get_role(823153343958351902)
        end = guild.get_role(842154406258147405)
        opts = []
        player_team = None
        for r in guild.roles:
            if not r in author.roles:
                if r.position < end.position and r.position > membership.position:

                    em = None
                    for e in guild.emojis:
                        try:
                            if r.name[-(len(e.name)):].lower() == e.name.lower():
                                em = e
                        except:
                            continue
                    option = SelectOption(label=r.name, value=json.dumps([str(em.name), str(r.name)]), emoji=str(em))
                    opts.append(option)
            else:
                player_team = r

        action = SelectMenu(
            custom_id="gametime_1",
            placeholder="Choose a team.",
            max_values=1,
            options=opts
        )

        await inter.create_response(
            content= "Which team are you playing against?",
            components= [action],
            ephemeral = True
        )

        inter = await int_bot.wait_for_dropdown()

        selected = json.loads(inter.select_menu.selected_options[0].value)
        emoji = discord.utils.find(lambda e: e.name == selected[0], inter.guild.emojis)
        role = discord.utils.find(lambda r: r.name == selected[1], inter.guild.roles)
    
        

        time_set = ActionRow(
            Button(label="AM", style= ButtonStyle.secondary),
            Button(label="PM",  style= ButtonStyle.secondary)
        )

        hours = ActionRow(
            Button(label="+1 hour", style= ButtonStyle.primary),
            Button(label="-1 hour",  style= ButtonStyle.primary)
        )

        tens = ActionRow(
            Button(label="+10 minutes",  style= ButtonStyle.primary),
            Button(label="-10 minutes", style= ButtonStyle.primary)
        )

        minutes = ActionRow(
            Button(label="+1 minutes", style= ButtonStyle.primary),
            Button(label="-1 minutes", style= ButtonStyle.primary)
        )

        confirm = ActionRow(
            Button(label="Confirm Game Time", style= ButtonStyle.green)
        )

        await inter.respond(type=7,
            content= "```What time will you be playing? Use the buttons to set the time.```\n\n``Currently Set Time``\n{}".format("12:00 AM EST"),
            ephemeral = True,
            components= [
                time_set,
                hours,
                tens,
                minutes,
                confirm
            ]
        )

        global time_thing
        time_thing = 0
        
        global t
        t = "AM"
        global listening
        listening = True

        async def update_msg(ty, val, int):
            global listening
            global time_thing
            global t
            if listening:
                if ty == "+":
                    time_thing += val
                elif ty == "-":
                    time_thing -= val
                else:
                    t = val
                
                hrs = max(0, min(12, time_thing//60))
                if hrs == 0:
                    hrs = 12
                mins = round(time_thing%60)
                if mins < 10:
                    mins = "0"+str(mins)

                await int.respond(type=7, 
                    content= "```What time will you be playing? Use the buttons to set the time.```\n\n``Currently Set Time``\n{}:{} {} EST".format(hrs, mins, t),
                    components= [
                        time_set,
                        hours,
                        tens,
                        minutes,
                        confirm
                    ]
                )
                

        @int_bot.event
        async def on_button_click(int):
            global time_thing
            global listening
            global t
            if int.component.label.endswith("hour"):
                if int.component.label[0] == "+":
                    await update_msg("+", 60, int)
                else:
                    await update_msg("-", 60, int)
            elif int.component.label.endswith("minutes"):
                if int.component.label[:3] == "+10":
                    await update_msg("+", 10, int)
                elif int.component.label[:3] == "-10":
                    await update_msg("-", 10, int)
                else:
                    if int.component.label[:2] == "+1":
                        await update_msg("+", 1, int)
                    else:
                        await update_msg("-", 1, int)
            elif int.component.label.endswith("M"):
               update_msg("m", int.component.label, int)
            else:
                await int.respond(type=7,
                    content= "***Your game has been scheduled and posted in game times.***"
                )
                listening = False


#@int_bot.slash_command()
async def updateinfo(inter, url= None, vc= False):
    info_channel = bot.get_channel(914703851800649769)
    info = await info_channel.fetch_message(917106041106366514)

    ## INFORMTATION ##
    embed = discord.Embed(title="Information", description= "Welcome to the *Handball: The League* information channel. This is where you can find important documents and resources for the league.\n\nTo access the resources, please select an option from the dropdown below.", colour= discord.Colour.blue())

    action = SelectMenu(
        custom_id="information",
        placeholder="Select an option.",
        max_values=1,
        options=[
            SelectOption(label= "Vanity Link", value="https://discord.gg/handball"),
            SelectOption(label= "Rulebook", value="https://docs.google.com/document/d/1VXrPnWmtphGJW8j6uFuSDvTo7sT5_x0NgW5hjICvybI/edit?usp=sharing"),
            SelectOption(label= "Statistics", value="https://docs.google.com/spreadsheets/d/1TFaIAtaDMKAm-9CsTuVd8qcATVSr8ZrFKSFbgJR4F0U/edit?usp=sharing"),
            SelectOption(label= "Handball Association v1.16", value= "https://www.roblox.com/games/7521555382/HBA-1-16"),
            SelectOption(label= "Main Game", value= "https://www.roblox.com/games/5498056786/Handball-Association"),
            SelectOption(label= "League Group", value= "https://www.roblox.com/groups/10195697/Handball-The-League#!/about"),
            SelectOption(label= "Team Owner Sign-Up", value= "https://forms.gle/s9qfRhkMPmU5XnVe6"),
            SelectOption(label= "Events Game", value= "https://www.roblox.com/games/6732385646/Handball-The-League"),
            SelectOption(label= "League YouTube", value= "https://www.youtube.com/channel/UCXdF-Z0u2NNiVNLjf1Oq2HA")
        ]
    )

    await info.edit(
        embed = embed,

        components=None
    )

@int_bot.slash_command(
    #options = [
    #    Option("team_one", "Enter the role of the team playing.", OptionType., required= True)
    #]
)
async def post_clip(inter, content):
    print(content)

@int_bot.slash_command(
    options = [
        Option("gametime", "What time is this game?", OptionType.STRING, required= True)
    ]
)
async def request(inter, gametime):
    author = inter.author
    htl = bot.get_guild(htl_servers["League"])

    if not coachCheck(author, htl):
        await inter.create_response(
            embed= error("Request", "Must be a team coach to use this command."),
            ephemeral= True
        )
        return

    team_check = teamCheck(author, htl)

    if not team_check[0]:
        await inter.create_response(
            embed= error("Request", "Must be on a team to use this command."),
            ephemeral= True
        )
        return

    embed = discord.Embed(title="Who are you requesting? Select from the dropdown.", description= "Requesting is limited to 1 request every hour per team.", colour= discord.Colour.blurple())

    await inter.create_response(
        embed= embed,
        components= [
            SelectMenu(
                custom_id="Request",
                placeholder="Select an option.",
                max_values=2,
                options=[
                    SelectOption(label= "Referee", value= "953293440198787093"),
                    SelectOption(label= "Streamer", value= "948415747116388362")
                ]
            )
        ],
        ephemeral= True
    )

    @int_bot.event
    async def on_dropdown(intera):
        if intera.component.custom_id != "Request":
            return

        team = teamCheck(author, htl)[1]

        selected = intera.select_menu.selected_options
        selected_str = []

        succ_embed = discord.Embed(title="Requesting...", description= "Your team is on cooldown for 1 hour.", colour= discord.Colour.blurple())
        
        for select in selected:
            selected_str.append(select.label)

        succ_embed.add_field(name= "``Requesting the Following``", value= " and ".join(selected_str))

        msg = await intera.create_response(
            embed = succ_embed,
            ephemeral = True
        )

        for job in selected:
            embed = discord.Embed(title="{} Needed".format(job.label), description= "Requesting is limited to 1 request every hour per team.", colour= discord.Colour.blurple())
            embed.add_field(name= "``Gametime``", value= gametime)
            embed.add_field(name= "``Team``", value= teamCheck(author, htl)[1].name, inline=False)
            embed.add_field(name= "``Coach``", value= author.name, inline=False)

            conn = psycopg2.connect(host= "ec2-23-23-162-138.compute-1.amazonaws.com", dbname="d2m6dv5ob6vvhd", user="yulopqnbwringk", password="554b54b2a437f704824a09b2602a68d1f7c9269e4307d7f4d71dcbd080736ce2")

            if True:
                with conn:
                    with conn.cursor() as cur:
                        try:
                            cur.execute("CREATE TABLE request_{}(id BIGINT, time INT)".format(job.label.lower()))
                            conn.commit()
                        except Exception:
                            pass
                            
                        conn.rollback()
                        cur.execute("SELECT * FROM request_{} where id= {}".format(job.label.lower(), team.id))

                        all_data = cur.fetchall()

                        data = None

                        for row in all_data:
                            if int(row[0]) == int(team.id):
                                data = row
                                break

                        current_time = round(time.time())

                        if data != None:
                            previous_time = data[1]

                            difference = current_time - previous_time

                            if not difference >= (60 * 30):
                                difference /= 60
                                difference /= 60

                                await inter.followup(
                                    embed= error("Request {}".format(job.label), "You can only use this command once every hour. You have last used this command {} hours ago.".format(round(difference, 2))),
                                    ephemeral = True
                                )

                                continue
                            else:
                                cur.execute("UPDATE request_{} SET time= {} where id= {}".format(job.label.lower(), current_time, team.id))

                        else:
                            cur.execute("INSERT INTO request_{}(id, time) VALUES ({}, {})".format(job.label.lower(), team.id, current_time))
                
                    conn.commit()

            channel_id = int(job.value)
            
            await bot.get_channel(channel_id).send(
                embed= embed,
                components = [
                    ActionRow(
                        Button(label= "Claim", style= ButtonStyle.primary, custom_id= "Claim {}".format(job.label))
                    )
                ],
                content= "@everyone"
            )

            @int_bot.event
            async def on_button_click(inter):
                if inter.component.custom_id == "Claim Streamer":
                    streamer = inter.author

                    embed = discord.Embed(title="Streamer Found", description= "A streamer has claimed your game.", colour= discord.Colour.red())
                    embed.add_field(name= "``Streamer``", value= "{} ({})".format(streamer.mention, streamer.name))

                    await author.send(embed= embed)

                    inter.component.disabled = True

                    embed = discord.Embed(title="Streamer Needed", description= "Requesting is limited to 1 request every hour per team.", colour= discord.Colour.blurple())
                    embed.add_field(name= "``Gametime``", value= gametime)
                    embed.add_field(name= "``Team``", value= teamCheck(author, htl)[1].name, inline=False)
                    embed.add_field(name= "``Coach``", value= author.name, inline=False)
                    embed.add_field(name= "``Claimed by...``", value= "{} ({})".format(streamer.mention, streamer.name), inline=False)

                    await inter.message.edit(
                        embed= embed,
                        components = []
                    )

                    await inter.create_response(
                        embed= discord.Embed(title="Claimed".format(job.label), description= "You have claimed this game. The coach that requested you will now be notified.", colour= discord.Colour.green()),
                        ephemeral= True
                    )
                elif inter.component.custom_id == "Claim Referee":
                    referee = inter.author

                    new_embed = discord.Embed(title="Referee Found".format(job.label), description= "A referee has claimed your game.", colour= discord.Colour.lighter_grey())

                    otherRefs = []
                    otherRefs.append("{} ({})\n".format(referee.mention, referee.name))

                    for embed in inter.message.embeds:
                        for field in embed.fields:
                            if field.name == "``Claimed by...``":
                                referees = field.value.split("\n")
                                for ref in referees:
                                    if ref.find(referee.name) > -1:
                                        await inter.create_response(
                                            embed= error("Claim Referee Spot", "You have already claimed this game."),
                                            ephemeral= True
                                        )

                                        return

                                    otherRefs.append(ref + "\n")

                    new_embed.add_field(name= "``Referee(s)``", value= "".join(otherRefs))

                    await author.send(embed= new_embed)

                    embed = discord.Embed(title="Referee Needed", description= "Requesting is limited to 1 request every hour per team.", colour= discord.Colour.blurple())
                    embed.add_field(name= "``Gametime``", value= gametime)
                    embed.add_field(name= "``Team``", value= teamCheck(author, htl)[1].name, inline=False)
                    embed.add_field(name= "``Coach``", value= author.name, inline=False)
                    embed.add_field(name= "``Claimed by...``", value= "".join(otherRefs), inline=False)

                    await inter.message.edit(
                        embed= embed
                    )

                    if len(otherRefs) >= 2:
                        await inter.message.edit(
                            embed= embed,
                            components= []
                        )
                    
                    await inter.create_response(
                        embed= discord.Embed(title="Claimed".format(job.label), description= "You have claimed this game. The coach that requested you will now be notified.", colour= discord.Colour.green()),
                        ephemeral= True
                    )


@int_bot.slash_command(
    options=[
        Option("team_one", "Enter the role of the team playing.", OptionType.ROLE, required= True),
        Option("team_two", "Enter the role of the team playing.", OptionType.ROLE, required= True),
        Option("stream_link", "Enter the stream link for your game.", OptionType.STRING, required= True)
    ]
)
async def post_stream(inter, team_one, team_two, stream_link):
    author = inter.author
    htl = bot.get_channel(htl_servers["League"])

    if not 922406011690700830 in author.roles:
        print(922406011690700830 in author.roles)
        await inter.create_response(
            embed= error("Post Stream", "You must be a streamer to use this command."),
            ephemeral= True
        )

        return

    if not team_role_check(team_one):
        await inter.create_response(
            embed= error("Post Stream", "\"{}\" is not a valid team.".format(team_one.name)),
            ephemeral= True
        )

        return
    
    if not team_role_check(team_two):
        await inter.create_response(
            embed= error("Post Stream", "\"{}\" is not a valid team.".format(team_two.name)),
            ephemeral= True
        )

        return

    if team_one == team_two:
        await inter.create_response(
            embed= error("Post Stream", "Both teams are the same."),
            ephemeral= True
        )

        return

    embed = discord.Embed(title="Stream Post Request", description= "Please review the information below. If you are ready to submit this request, press the green button. If not, press the red button. A Director+ will receive this request and will be allowed to approve/decline it.", colour= discord.Colour.red())
    embed.add_field(name= "``Game``", value= "**{}** *vs* **{}**".format(team_one.name, team_two.name))
    embed.add_field(name= "``Stream Link``", value= stream_link)
    await inter.create_response(
        embed= embed,
        components= [
            ActionRow(
                Button(label="✅",  style= ButtonStyle.green),
                Button(label="❌",  style= ButtonStyle.red)
            )
        ],
        ephemeral= True
    )


    @int_bot.event
    async def on_button_click(int):
        if int.component.label == "✅":
            pass
        else:
            await inter.create_response(
                embed= error("Post Stream", "Cancelling."),
                ephemeral= True
            )

@int_bot.slash_command(
    options= [
        Option("emoji", "Enter emoji here.", OptionType.STRING, required=True)
    ]
)
async def get_emoji_color(inter, emoji):
    emoji = find_emojis(emoji)[0]
    emoji_file = await emoji.url.save("cached_data/cached_emoji")

    cf = ColorThief("cached_data/cached_emoji")

    rgb = cf.get_color()

    hex = rgb_to_hex(rgb)

    embed = discord.Embed(title="Roles", description= "Gain roles by reacting with the respective emoji.", colour= discord.Color.from_rgb(rgb[0], rgb[1], rgb[2]))
    embed.add_field(name= "``Emoji``", value= emoji)
    embed.add_field(name= "``HEX``", value= "#"+hex)

    await inter.create_response(
        embed= embed,
        ephemeral= True
    )

    os.remove("cached_data/cached_emoji")


@int_bot.slash_command()
async def roles(inter):
    author = inter.author
    guild = inter.guild

    if not guild.get_role(910373792176554016) in author.roles:
        return


    # REACTION ROLES #

    embed = discord.Embed(title="Roles", description= "Gain roles by reacting with the respective emoji.", colour= discord.Colour.blue())
    embed.add_field(name= "🔰 ``Team Owner Queue``", value= "*React using the 🔰 emoji to ENABLE notifications regarding open Team Owner positions.*", inline= False)
    embed.add_field(name= "🚫 ``Disable Partnerships``", value= "*React using the 🚫 emoji to DISABLE the partnerships channel and its notifications.*", inline= False)
    embed.add_field(name= "📺 ``Disable Streams``", value= "*React using the 📺 emoji to DISABLE the streams channel and its notifications.*", inline= False)
    embed.add_field(name= "🤾 ``Enable Pickups``", value= "*React using the 🤾 emoji to ENABLE the pickups channel and its notifications.*", inline= False)
    embed.add_field(name= "🎮 ``Enable Gamenights``", value= "*React using the 🎮 emoji to ENABLE the gamenights channel and its notifications.*", inline= False)
    embed.add_field(name= "📰 ``Media Ping``", value= "*React using the 📰 emoji to ENABLE media notifications (⚠️ You may receive frequent notifications with this role).*", inline= False)

    await inter.channel.send(
        embed = embed
    )
    
@int_bot.slash_command(
    description= "Resources.",
    options=[
        Option("channel", "Which channel needs it's info embeds?", OptionType.CHANNEL, required= True)
    ]
)
async def resources(inter, channel):
    author = inter.author
    guild = inter.guild

    if not guild.get_role(910373792176554016) in author.roles:
        return

    channels = {
        'Links': 914703851800649769,
        'Rosters': 948053321875353660,
        'Roles': 944094182631407636,
        'Stats Archive': 948055093192847420,
        'Help': 948055826894053446
    }

    for channel_name, channel_id in channels.items():
        if channel.id == channel_id:
            embed = discord.Embed(title=channel_name, description= "Welcome to *Handball: The League*.", colour= discord.Colour.gold())
            embed.set_image(url= "https://media.discordapp.net/attachments/900196855663689730/947345003280203846/Handball_Thumbnail.png?width=822&height=462")

            await channel.send(embed=embed)
            break

    if channel.id == channels["Links"]:
        # ROBLOX LINKS #
        embed = discord.Embed(title="Roblox Links", description= "", colour= discord.Colour.light_grey())

        action = SelectMenu(
            custom_id="information",
            placeholder="Select an option.",
            max_values=1,
            options=[
                SelectOption(label= "League Group", value= "https://www.roblox.com/groups/10195697/Handball-The-League#!/about"),
                SelectOption(label= "Handball Association", value= "https://www.roblox.com/games/5498056786/Handball-Association"),
                SelectOption(label= "HTL Events", value= "https://www.roblox.com/games/6732385646/Handball-The-League")
            ]
        )

        await channel.send(
            embed= embed,
            components=[action]
        )

        # LEAGUE FILES #
        embed = discord.Embed(title="League Files", description= "", colour= discord.Colour.dark_grey())

        action = SelectMenu(
            custom_id="information",
            placeholder="Select an option.",
            max_values=1,
            options=[
                SelectOption(label= "Rulebook", value="https://docs.google.com/document/d/1NK3pw-e5EojJOTNzIQCjkG5hY5P6YbircnLlQH6Rc5A/edit?usp=sharing"),
                SelectOption(label= "Main Sheet", value="https://docs.google.com/spreadsheets/d/1TFaIAtaDMKAm-9CsTuVd8qcATVSr8ZrFKSFbgJR4F0U/edit?usp=sharing")
            ]
        )

        await channel.send(
            embed= embed,
            components=[action]
        )

        # APPLICATIONS #
        embed = discord.Embed(title="Applications", description= "", colour= discord.Colour.red())

        action = SelectMenu(
            custom_id="information",
            placeholder="Select an option.",
            max_values=1,
            options=[
                SelectOption(label= "Team Owner", value="https://forms.gle/UV8WAfYVA5yD7jaX8"),
                SelectOption(label= "Streamer", value="https://forms.gle/nqoKMc87xJGZer5AA"),
                SelectOption(label= "Media", value= "https://forms.gle/LXXdmS5vWwQ3ZhYq7"),
                #SelectOption(label= "Gamenight/Pickups Host", value= "__**HTL Is Looking for Event Hosts!**__\n\nYou **MUST** meet the following requirements to become an Event Host:\n- For those interested in hosting pickups, you must know how to run an Handball Association private server.\n- You must be active as an event host.\n\nIf you meet the listed requirements, you may message {} to become an Event Host.".format("<@!708373801615753295>"))
                SelectOption(label= "Referee", value= "https://forms.gle/b9MqJcPSiuoXaACE8"),
                #SelectOption(lable= "")

            ]
        )

        await channel.send(
            embed= embed,
            components=[action]
        )

        # Social Media #
        embed = discord.Embed(title="Social Media", description= "", colour= discord.Colour.blurple())

        action = SelectMenu(
            custom_id="information",
            placeholder="Select an option.",
            max_values=1,
            options=[
                SelectOption(label= "League YouTube", value= "https://www.youtube.com/channel/UCXdF-Z0u2NNiVNLjf1Oq2HA")
            ]
        )

        await channel.send(
            embed= embed,
            components=[action]
        )

    elif channel.id == channels["Rosters"]:
        # TEAM COACHES #
        embed = discord.Embed(title="Team Coaches", description= "Select a team below to view a list of their Team Coaches.", colour= discord.Colour.blue())

        membership = guild.get_role(917043822402338886)
        end = guild.get_role(917043508509032508)
        opts = []

        for r in guild.roles:
            if not r in author.roles:
                if r.position < end.position and r.position > membership.position:
                    em = None
                    for e in guild.emojis:
                        try:
                            if r.name[-(len(e.name)):].lower() == e.name.lower():
                                em = e
                        except:
                            continue
                    
                    option = None
                    try:
                        option = SelectOption(label=r.name, value=json.dumps([str(em.name), str(r.name)]), emoji=str(em))
                    except:
                        option = SelectOption(label=r.name, value=json.dumps(["", str(r.name)]))
                    opts.append(option)


        action = SelectMenu(
            custom_id="team coaches",
            placeholder="Select a team.",
            max_values=1,
            options=opts
        )

        await channel.send(
            embed= embed,
            components=[action]
        )

        # MEMBERS #
        opts = []

        for r in guild.roles:
            if not r in author.roles:
                if r.position < end.position and r.position > membership.position:
                    em = None
                    for e in guild.emojis:
                        try:
                            if r.name[-(len(e.name)):].lower() == e.name.lower():
                                em = e
                        except:
                            continue
                    
                    option = None
                    try:
                        option = SelectOption(label=r.name, value=json.dumps([str(em.name), str(r.name)]), emoji=str(em))
                    except:
                        option = SelectOption(label=r.name, value=json.dumps(["", str(r.name)]))
                    opts.append(option)

        action = SelectMenu(
            custom_id="members",
            placeholder="Choose a team.",
            max_values=1,
            options=opts
        )

        embed = discord.Embed(title="Team Rosters", description= "Select a team below to view their roster.", colour= discord.Colour.blue())

        await channel.send(
            embed = embed,
            components = [action]
        )

    elif channel.id == channels["Stats Archive"]:
        leagues = {
            'Handball Association': {
                'Season 1': "https://docs.google.com/spreadsheets/d/1bxNPHuIyFYqNIkH_mbLzkdN1d-ymH37NL1F_vLNsU88/edit?usp=sharing",
                'Season 2': "https://docs.google.com/spreadsheets/d/1QjfSL8CnoDnM7TasytWkTAKZh4N5ydZQElHhB5FVyso/edit?usp=sharing"
            },

            'Handball: The League v1': {
                'Season 1': "https://docs.google.com/spreadsheets/d/1pp5OuPtctRJ56g1FsMmbCDTVHVUfj7Ndtnf3lHvY-r0/edit?usp=sharing",
                'Season 2': "https://docs.google.com/spreadsheets/d/1FP6lWNJmI-TleebDgP_1Ia8fKfovl4WVnC6cTBQAjbM/edit?usp=sharing",
                'Season 3': "https://docs.google.com/spreadsheets/d/1NOFvEUbyoHGxMhKXE5A6MPWO7BdMy0q4g6D-aH5uCSI/edit?usp=sharing",
                'Season 4': "Stats for Season 4 have been lost."
            },

            'Handball: The League v2': {
                'Season 1': "Stats for Season 1 have been lost.",
                'Season 2': "Coming soon..."
            }
        }

        for league, league_data in leagues.items():
            embed = discord.Embed(title=league, description= "", colour= discord.Colour.light_grey())

            options = []

            for season, stats in league_data.items():
                options.append(SelectOption(label= season, value=stats))

            action = SelectMenu(
                custom_id="information",
                placeholder="Select an option.",
                max_values=1,
                options=options
            )

            await channel.send(
                embed= embed,
                components=[action]
            )

@int_bot.slash_command()
async def media_ping(inter):
    channel = inter.channel

    if not channel.category_id == 916129517830037515:
        await inter.create_response(
            embed= error("Media Ping", "Command must be used in a media channel."),
            ephemeral= True
        )
        return

    try:
        conn = psycopg2.connect(host= "ec2-23-23-162-138.compute-1.amazonaws.com", dbname="d2m6dv5ob6vvhd", user="yulopqnbwringk", password="554b54b2a437f704824a09b2602a68d1f7c9269e4307d7f4d71dcbd080736ce2")

        with conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("CREATE TABLE mediaPings(id BIGINT, time INT)")
                except Exception:
                    pass
                    
                conn.rollback()
                cur.execute("SELECT * FROM mediaPings where id= {}".format(channel.id))

                all_data = cur.fetchall()

                data = None

                for row in all_data:
                    if int(row[0]) == int(channel.id):
                        data = row
                        break

                current_time = round(time.time())

                if data != None:
                    previous_time = data[1]

                    difference = current_time - previous_time

                    if not difference >= (60 * 120):
                        difference /= 60
                        difference /= 60

                        await inter.create_response(
                            embed= error("Media Ping", "You can only use this command once every 2 hours. You have last used this command {} hours ago.".format(round(difference, 2))),
                            ephemeral = True
                        )

                        conn.commit()

                        return
                    else:
                        cur.execute("UPDATE mediaPings SET time= {} where id= {}".format(current_time, channel.id))

                else:
                    cur.execute("INSERT INTO mediaPings(id, time) VALUES ({}, {})".format(channel.id, current_time))
        
            conn.commit()

        await bot.get_channel(channel.id).send("*New media notification, <@&944096313966989342>! You may unsubscribe to media pings in <#944094182631407636>.*")
        await inter.create_response(embed= discord.Embed(title="Success", colour= discord.Colour.green()), ephemeral= True)
    except Exception:
       await inter.create_response(embed= error("Media Ping", "Command unexpectedly error'd."), ephemeral= True)
    
"""    
@int_bot.slash_command(
    description="Perform transactions on players",
    options=[
        Option("user", "Who are you using this transaction on?", OptionType.USER, required=True),
        Option("transaction", "What kind of transaction is this?", OptionType.STRING, required=True),
        Option("team", "What is the primary team of this transaction?", OptionType.ROLE, required=True)
        #Option("secondary team", "Is there a secondary team for this transaction?", OptionType.ROLE, required=False),
        
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def transaction(inter, user=None):
    # If user is None, set it to inter.author
    print(user)
    user = user or inter.author
    # We are guaranteed to receive a discord.User object,
    # because we specified the option type as Type.USER

    emb = discord.Embed(
        title=f"{user}'s avatar",
        color=discord.Color.blue()
    )
    emb.set_image(url=user.avatar_url)
    await inter.reply(embed=emb)
"""

@int_bot.event
async def on_dropdown(inter: int_bot):
    if inter.component.custom_id == "members":
        guild = inter.guild
        team = inter.select_menu.selected_options[0]

        role = [discord.utils.get(guild.roles, name=team.label) for r in guild.roles][0]

        embed = discord.Embed(title=role.name, description= "List of members in {}".format(role.name), colour=role.colour)

        embed.add_field(name= "``# of Members``", value= "{} members.".format(len(role.members)), inline= False)

        for x in role.members:
            if guild.get_role(917068655928442930) in x.roles:
                embed.add_field(name= "``Team Owner``", value= x.mention + "({})".format(x.name + "#" + x.discriminator))
            elif guild.get_role(917068674626646027) in x.roles:
                embed.add_field(name= "``Head Coach``", value= x.mention + "({})".format(x.name + "#" + x.discriminator))
            elif guild.get_role(917068697334595664) in x.roles:
                embed.add_field(name= "``Assistant Coach``", value= x.mention + "({})".format(x.name + "#" + x.discriminator))
            else:
                embed.add_field(name= "``Member``", value= x.mention + "({})".format(x.name + "#" + x.discriminator))

        await inter.create_response(
            embed= embed,
            ephemeral = True
        )
    elif inter.component.custom_id == "information":
        label = inter.select_menu.selected_options[0]

        embed = discord.Embed(title="{}".format(label.label), colour= discord.Colour.orange())

        embed.add_field(name= "``Data``", value= label.value)

        await inter.create_response(
            embed= embed,
            ephemeral = True
        )
    elif inter.component.custom_id == "team coaches":
        team = inter.select_menu.selected_options[0]

        guild = inter.guild

        team = [discord.utils.get(guild.roles, name=team.label) for r in guild.roles][0]
        
        embed = discord.Embed(title= team.name, colour= team.colour)

        for x in team.members:
            if guild.get_role(917068655928442930) in x.roles:
                embed.add_field(name= "``Team Owner``", value= x.mention + "({})".format(x.name + "#" + x.discriminator), inline=False)
            elif guild.get_role(917068674626646027) in x.roles:
                embed.add_field(name= "``Head Coach``", value= x.mention + "({})".format(x.name + "#" + x.discriminator), inline=False)
            elif guild.get_role(917068697334595664) in x.roles:
                embed.add_field(name= "``Assistant Coach``", value= x.mention + "({})".format(x.name + "#" + x.discriminator), inline=False)

        await inter.create_response(
            embed= embed,
            ephemeral = True
        )



@int_bot.slash_command(description="Provides the stats sheet.")
async def stats(inter):
    await inter.create_response(
        content = "https://docs.google.com/spreadsheets/d/1TFaIAtaDMKAm-9CsTuVd8qcATVSr8ZrFKSFbgJR4F0U/edit?usp=sharing",
        ephemeral = True
    )


# Log in
bot.run(token)