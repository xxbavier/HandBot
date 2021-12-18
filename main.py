from datetime import time
import re
from aiohttp.client_reqrep import ContentDisposition
import discord
from discord import player
from discord.embeds import Embed
from discord.ext import commands, tasks
from discord.utils import parse_time
from dislash import InteractionClient, ActionRow, Button, ButtonStyle, SelectMenu, SelectOption, ContextMenuInteraction, Option, OptionType
from dislash.interactions.message_components import Component

import requests

import keep_alive
import json
from itertools import cycle
import sqlite3
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
  if(msg.channel.id == 917102767208816680):
    #return
    global coach
    coach = False
    roleId = 0

    membership = msg.guild.get_role(917043822402338886)
    end = msg.guild.get_role(917043508509032508)

    for x in msg.author.roles:
      if x.id == 917068655928442930 or x.id == 917068674626646027 or x.id == 917068697334595664:
        coach = True
        roleId = x.id

    if not coach:
      return

    emoji = re.findall(r'<:\w*:\d*>', msg.content)
    emoji = [int(e.split(':')[2].replace('>', '')) for e in emoji]
    emoji = [discord.utils.get(msg.guild.emojis, id=e) for e in emoji]
    emoji = emoji[0]

    role = None

    players = msg.mentions

    if len(players) <= 0:
      return

    args = msg.content.split(' ')

    if len(args) <= 2:
      return


    for x in msg.guild.roles:
      if x.name.endswith(emoji.name):
          if x.position < end.position and x.position > membership.position:
            role = x
            break
    
    if role:
      if not role in msg.author.roles:
        return

      embed= discord.Embed(title= "{}".format(role.name), description= "Transaction for {}.".format(role.name), colour= discord.Colour.green())

      eligible = []

      
      for x in players:
        if not x.bot:

          if args[1].lower() == "promote" or args[1].lower() == "demote":
            eligible.append(x)
          else:
            if not msg.author == x:
              teams = []
              if not args[1].lower() == "release":
                for r in x.roles:
                  if r.position < end.position and r.position > membership.position:
                    teams.append(r)
                
                if len(teams) == 0:
                  eligible.append(x)
              else:
                  eligible.append(x)

        
      

      if len(eligible) == 0:
        embed.add_field(name= "``Error``", value= "Unable to sign the players mentioned. They may already be signed to a team. If you tried using the command on yourself, this is not allowed.")
        embed.colour = discord.Colour.red()

        await msg.channel.send(embed= embed)

        return


      if args[1].lower() == "sign":
        roled = ""
        capped = ""
        for x in eligible:
          if len(role.members) < 16:
            await x.add_roles(role)
            roled += x.mention+", "
          else:
            capped += x.mention+", "
        
        embed.add_field(name="``Added the following players``", value= roled, inline=False)
        if len(capped) > 0:
          embed.add_field(name= "``Unable to sign the following players due to player cap``", value= capped)
        embed.add_field(name= "``Team Size``", value= len(role.members))

      elif args[1].lower() == "release":
        roled = ""
        for x in eligible:
          await x.remove_roles(role)
          roled += x.mention+", "

          await x.remove_roles(msg.guild.get_role(917068674626646027))
          await x.remove_roles(msg.guild.get_role(917068697334595664))
        
        embed.add_field(name="``Removed the following players``", value= roled, inline=False)
      
      elif args[1].lower() == "promote" or args[1].lower() == "demote":
        if not role in eligible[0].roles:
          return

        if not roleId == 917068655928442930:
          embed.colour = discord.Colour.red()
          embed.add_field(name= "``Missing Permission``", value= "Only Team Owners may promote/demote players.")

          await msg.channel.send(embed= embed)
          return
        if len(args) >= 4:
          if args[3].lower() == "hc":
            await eligible[0].add_roles(msg.guild.get_role(917068674626646027))
            await eligible[0].remove_roles(msg.guild.get_role(917068697334595664))

            embed.add_field(name="``Promoted the following player to Head Coach``", value= eligible[0].mention, inline=False)
          elif args[3].lower() == "ac":
            await eligible[0].add_roles(msg.guild.get_role(917068697334595664))
            await eligible[0].remove_roles(msg.guild.get_role(917068674626646027))

            embed.add_field(name="``Promoted the following player to Assistant Coach``", value= eligible[0].mention, inline=False)
          else:
            await eligible[0].remove_roles(msg.guild.get_role(917068697334595664))
            await eligible[0].remove_roles(msg.guild.get_role(917068674626646027))

            embed.add_field(name="``Demoted the following player from coaching``", value= eligible[0].mention, inline=False)
        else:
          await eligible[0].remove_roles(msg.guild.get_role(917068697334595664))
          await eligible[0].remove_roles(msg.guild.get_role(917068674626646027))

          embed.add_field(name="``Demoted the following player from coaching``", value= eligible[0].mention, inline=False)
      else:
        if not roleId == 917068655928442930:
          embed.colour = discord.Colour.red()
          embed.add_field(name= "``Error``", value= "Sorry but I did not understand what transaction type this message was. Please follow the format: \"<emoji> (sign/release/promote/demote) <mentions of player(s)> (HC/AC, if applicable)\"")

    await msg.channel.send(embed= embed)
          
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

events_channel = 900511820643725312      
@int_bot.slash_command(
    description= "Post a gamenight",
    options=[
        Option("url", "Enter the gamenight URL", OptionType.STRING, required= True),
        Option("vc", "Will this gamenight be in a VC as well? T/F", OptionType.BOOLEAN)
        # By default, Option is optional
        # Pass required=True to make it a required arg
    ]
)
async def gamenight(inter, url= None, vc= False):
    valid_domains = [
        "roblox",
        "skribbl"
    ]

    author = inter.author
    guild = inter.guild

    valid = False

    for role in author.roles:
        if role.name.find("Community"):
            valid = True
            
    if not valid:
        embed = discord.Embed(title="Error", description= "You do not have permission to run this command.", colour= discord.Colour.red())

        await inter.create_response(
            embed= embed,
            ephemeral = True
        )
        return

    try:
        response = requests.get(url)
    except:
        embed = discord.Embed(title="Error", description= "Invalid URL.", colour= discord.Colour.red())
        await inter.create_response(
            embed= embed,
            ephemeral = True
        )
        return
    
    valid_url = False

    for domain in valid_domains:
        if url.find(domain):
            valid_url = True

    if not valid_url:
        embed = discord.Embed(title="Error", description= "Invalid URL domain.", colour= discord.Colour.red())

        list_of_domains = ""

        for domain in valid_domains:
            list_of_domains += "\n- *()*".format(domain)
        
        list_of_domains += "\n- *More coming soon...*"

        embed.add_field(name= "``List of Valid Domains``", value= list_of_domains)

        await inter.create_response(
            embed= embed,
            ephemeral = True
        )

        return
    
    embed = discord.Embed(title="Sending...", description= "Your gamenight is being posted.", colour= discord.Colour.green())

    await inter.create_response(
        embed= embed,
        ephemeral = True
    )

    embed = discord.Embed(title="New Gamenight!", description= "New gamenight hosted by {}.".format(author.mention), colour= discord.Colour.blurple())

    def in_vc():
        if vc:
            return "This gamenight will be using a Voice Channel."
        else:
            return "This gamenight will not be using a Voice Channel."

    embed.add_field(name="``Voice Channel?``", value= in_vc())

    await bot.get_channel(events_channel).send(
        content= "<@&900551881003237426>",
        embed= embed
    )

    await bot.get_channel(events_channel).send(
        content= url
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

    # REACTION ROLES #

    embed = discord.Embed(title="Roles", description= "Gain roles by reacting with the respective emoji.", colour= discord.Colour.blue())
    embed.add_field(name= "🚫 ``Disable Partnerships``", value= "*React using the 🚫 emoji to DISABLE the partnerships channel and its notifications.*", inline= False)
    embed.add_field(name= "📺 ``Disable Streams``", value= "*React using the 📺 emoji to DISABLE the streams channel and its notifications.*", inline= False)
    embed.add_field(name= "🤾 ``Enable Pickups``", value= "*React using the 🤾 emoji to ENABLE the pickups channel and its notifications.*", inline= False)
    embed.add_field(name= "🎮 ``Enable Gamenights``", value= "*React using the 🎮 emoji to ENABLE the gamenights channel and its notifications.*", inline= False)

    await inter.channel.send(
        embed = embed
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