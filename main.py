from datetime import time
from dis import disco
from email import message
from urllib import response
import discord
from discord import player
from discord.embeds import Embed
from discord.ext import commands, tasks
from discord.utils import parse_time
from dislash import InteractionClient, ActionRow, Button, ButtonStyle, SelectMenu, SelectOption, ContextMenuInteraction, Option, OptionType
from dislash.interactions.message_components import Component
import psycopg2

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

transactions_id = 917102767208816680

teamOwner = 917068655928442930
headCoach = 917068674626646027
assistantCoach = 917068697334595664

demands = {
    2: 942302221696135198,
    1: 942302278054985808,
    0: 942302302037999616
}

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

def teamCheck(user, htl):
    '''
    Checks to see if a player is on a valid team.
    
    Returns True if player is on a team.
    Returns False if player is not on a team.
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
    embed = discord.Embed(title="ERROR", description= "There was an error while executing this command.", colour= discord.Colour.red())
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
    if (msg.content.startswith('<:twitter:831307974533316648>')):
      verified =  True
      for role in msg.author.roles:
        if role.id == 823156809795633154:
          verified =  False
      
      if verified:
        await msg.add_reaction('<:verified:831316205745733672>')
      
      await msg.add_reaction('❤️')
      await msg.add_reaction('<:repost:831318107574370365>')
      
    else:
      await msg.delete()
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
    htl = inter.guild

    coach_level = coachCheck(author, htl)
    team_info = teamCheck(author, htl)

    valid_team = team_info[0]
    team_role = team_info[1]
    
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
    htl = inter.guild

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
    htl = inter.guild

    team_info = teamCheck(author, htl)
    coach_info = coachCheck(author, htl)
    demands_info = get_demands(author, htl)

    if coach_info == 3 or not team_info[0]:
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
    htl = inter.guild

    coach_level = coachCheck(author, htl)
    team_info = teamCheck(author, htl)

    valid_team = team_info[0]
    team_role = team_info[1]
    
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
    htl = inter.guild

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
    htl = inter.guild

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

@int_bot.slash_command(description="Info.")
async def information(inter):
    author = inter.author
    guild = inter.guild

    if not guild.get_role(910373792176554016) in author.roles:
        return

    # INFORMATION #

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

    await inter.channel.send(
        embed= embed,
        components=[action]
    )

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

    await inter.channel.send(
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

    await inter.channel.send(
        embed = embed,
        components = [action]
    )
    
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