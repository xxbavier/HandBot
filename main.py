from datetime import time
from aiohttp.client_reqrep import ContentDisposition
import discord
from discord import player
from discord.ext import commands, tasks
from discord.utils import parse_time
from dislash import InteractionClient, ActionRow, Button, ButtonStyle, SelectMenu, SelectOption, ContextMenuInteraction, Option, OptionType
from dislash.interactions.message_components import Component

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
int_bot = InteractionClient(bot, test_guilds=[885265675365548112, 823037558027321374], modify_send= True)

status = cycle(['Handball','Xavs Simulator'])


@int_bot.event
async def on_ready():
  change_status.start()
  print("Your bot is ready")

@tasks.loop(seconds=30)
async def change_status():
  await bot.change_presence(activity=discord.Game(next(status)))

# Main
"""
with open('stuff.json', "r") as f:
    config = json.loads(f.read())
token = config.get('token')
"""

@int_bot.slash_command(description= "Submit your game time.")
async def gametime(inter):
    def check(user):
        to = inter.guild.get_role(823191636149534751)
        hc = inter.guild.get_role(823191733273493504)
        ac = inter.guild.get_role(823191767457202226)

        if to in user.roles or hc in user.roles or ac in user.roles:
            return True
        else:
            return False

    author = inter.author

    if check(author):
        guild = await bot.fetch_guild(823037558027321374)

        channel = guild.get_channel(891550181269598219)

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

                
                

                
@int_bot.slash_command(description="Info.")
async def information(inter):
    author = inter.author
    guild = inter.guild

    if not guild.get_role(823138967251189840) in author.roles:
        return

    # INFORMATION #

    embed = discord.Embed(title="Information", description= "Welcome to the *Handball: The League* information channel. This is where you can find important documents and resources for the league.\n\nTo access the resources, please select an option from the dropdown below.", colour= discord.Colour.blue())

    action = SelectMenu(
        custom_id="information",
        placeholder="Select an option.",
        max_values=1,
        options=[
            SelectOption(label="Vanity Link", value="https://discord.gg/handball"),
            SelectOption(label="Rulebook", value="https://docs.google.com/document/d/1VXrPnWmtphGJW8j6uFuSDvTo7sT5_x0NgW5hjICvybI/edit?usp=sharing"),
            SelectOption(label="Statistics", value="https://docs.google.com/spreadsheets/d/1TFaIAtaDMKAm-9CsTuVd8qcATVSr8ZrFKSFbgJR4F0U/edit?usp=sharing"),
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

    membership = guild.get_role(823153343958351902)
    end = guild.get_role(842154406258147405)
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
                option = SelectOption(label=r.name, value=json.dumps([str(em.name), str(r.name)]), emoji=str(em))
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
    membership = guild.get_role(823153343958351902)
    end = guild.get_role(842154406258147405)

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
            if guild.get_role(823191636149534751) in x.roles:
                embed.add_field(name= "``Team Owner``", value= x.mention + "({})".format(x.name + "#" + x.discriminator))
            elif guild.get_role(823191733273493504) in x.roles:
                embed.add_field(name= "``Head Coach``", value= x.mention + "({})".format(x.name + "#" + x.discriminator))
            elif guild.get_role(823191767457202226) in x.roles:
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
            if guild.get_role(823191636149534751) in x.roles:
                embed.add_field(name= "``Team Owner``", value= x.mention + "({})".format(x.name + "#" + x.discriminator), inline=False)
            elif guild.get_role(823191733273493504) in x.roles:
                embed.add_field(name= "``Head Coach``", value= x.mention + "({})".format(x.name + "#" + x.discriminator), inline=False)
            elif guild.get_role(823191767457202226) in x.roles:
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