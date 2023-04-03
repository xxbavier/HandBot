import os
import discord
from discord import app_commands, ui
from typing import List
import threading
import random
import roblox
import json
import asyncio
from flask import Flask
from flask_restful import Api, Resource, reqparse
from settings import htl_servers
from Modules.teamRoles import *
from Commands import account, admin, elo, free_agency, market, medals, moderation, teams
from inspect import getmembers, isfunction, isclass
from Commands.free_agency import FA_Post
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

app = Flask(__name__)
api = Api(app)

tree = bot.tree

def get_roles(member: discord.Member, adding_roles: bool):
    roles = [
        ["🤾", "Pickup Pings", 917051613196193812],
        ["🎮", "Event Pings", 917051775754829874],
        ["📺", "Stream Pings", 1088688412850135112],
        ["🚫", "Mute Partnerships", 917051682343501884],
        ["🔰", "Team Owner Interest", 944096262779719681]
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

@bot.event
async def on_interaction(inter: discord.Interaction):
    data = inter.data

    try:
        id = data["custom_id"]
        
        if data["component_type"] != 2:
            values = data["values"]
    except Exception:
        return

    if id.split(" ")[0] == "account":
        await account.handle_interaction(inter)

    if id == "Information":
        embed = discord.Embed(title= values[0])
        view = None

        if values[0] == "Introduction":
            embed.description = "*Welcome to the biggest Handball league on the Roblox platform, Handball: The League. HTL is a NA-based league that was established in March of 2021.*\n\n**This channel is where you can find information about the league.**"
        elif values[0] == "Getting Started":
            embed.description = "*Upon joining the league, there are a few ways for new players to involve themselves in the league.*"

            class gettingStarted(ui.View):
                @ui.select(options=[
                    discord.SelectOption(label= "Tournaments", emoji="🏆", value = "Tournaments"),
                    discord.SelectOption(label= "Pickups", emoji="🥅", value = "Pickups"),
                    discord.SelectOption(label= "Free Agency", emoji="🔰", value = "Free Agency"),
                    discord.SelectOption(label= "Chat", emoji="💬", value = "Chat"),
                ], placeholder= "Find ways to get started.", custom_id= "Getting Started")
                async def callback():
                    pass

            view = gettingStarted()
                
        elif values[0] == "League Invite":
            invite = await inter.channel.create_invite(
                reason= "Information channel",
                max_age=0,
                max_uses=0,
                unique=False
            )

            embed.add_field(name= "``Permanent``", value= invite.url, inline= False)
            
            vanity = inter.guild.vanity_url

            if not vanity:
                vanity = "HTL does not have a vanity invite at the moment."

            embed.add_field(name= "Vanity", value= vanity, inline= False)

        elif values[0] == "Game":
            embed.description = "Click the buttons to access the Roblox sites."

            view = ui.View()

            game = ui.Button(label= "Game Page", url= "https://www.roblox.com/games/5498056786/Handball-Association", style= discord.ButtonStyle.gray)
            group = ui.Button(label= "League Group Page", url= "https://www.roblox.com/groups/10195697/Handball-The-League", style= discord.ButtonStyle.red)

            view.add_item(game)
            view.add_item(group)

        elif values[0] == "Rulebook":
            embed.description = "Click the buttont to access the HTL Rulebook."

            view = ui.View()
            
            rulebook = ui.Button(label= "Rulebook", url= "https://docs.google.com/document/d/1NK3pw-e5EojJOTNzIQCjkG5hY5P6YbircnLlQH6Rc5A/edit?usp=sharing")

            view.add_item(rulebook)

        elif values[0] == "Roles":
            #embed.description = "*This module is not yet finished. You subscribe to roles in <#944094182631407636> for now.*"

            view = ui.View()

            add_roles = ui.Button(custom_id= "Add Roles", label= "Add Roles", style= discord.ButtonStyle.green)
            remove_roles = ui.Button(custom_id= "Remove Roles", label= "Remove Roles", style= discord.ButtonStyle.red)

            view.add_item(add_roles)
            view.add_item(remove_roles)
        
        elif values[0] == "Applications":
            embed.description = "*This module is not yet finished.*"

            #@ui.select()
        
        await inter.response.send_message(embed= embed, ephemeral= True, view= view)

    elif id == "Getting Started":
        embed = discord.Embed(title = values[0])
        view = None

        if values[0] == "Tournaments":
            embed.description = "**Every week or two, we host tournaments that are fully randomized (random bracket and random teams).**\n\n> *In tournaments, you are guarenteed playtime and will be competing for a Robux prize.*\n\n__Tournaments Channel:__ <#1054697507332046849>"
        elif values[0] == "Pickups":
            embed.description = "**Pickup games are mock games ran by the community.**\n\n> *Pickups are a great way to get yourself involved in HTL and to get others to notice your skill.*"
        elif values[0] == "Free Agency":
            embed.description = "**Teams are often looking for new players for their rosters and like to scout new players.**\n\n> *You can get noticed by posting a Free Agency advertisement using the Handbot or by responding to posts made by Team Coaches in the scouting channel.*"

            class freeAgencyView(ui.View):
                @ui.button(label= "Post Free Agent Ad", style= discord.ButtonStyle.blurple)
                async def callback(self, inter: discord.Interaction, extra):
                    await inter.response.send_modal(FA_Post())

            view = freeAgencyView()

        elif values[0] == "Chat":
            embed.description = "**Talking to other members in the league and forming connections is a good way to get involved in the league.**\n\n> *Some teams tend to tryout/recruit members that are active in the community; in addition, forming connections is a good way to form a team if a member is interested in owning a team.*"

        await inter.response.send_message(embed= embed, ephemeral= True, view=view)
    
    elif id == "Delete Pickup":
        embed = inter.message.embeds[0]
        embed.title = "This Pickup Has Concluded!"
        embed.set_image(url= None)

        if str(inter.user.id) != inter.message.embeds[0].author.name:
            raise Exception("You do not have permission to do this!")

        await inter.message.edit(embed= embed, view= None)

    elif id == "Ping Again":
        if str(inter.user.id) != inter.message.embeds[0].author.name or inter.guild.get_role(917055936349233272) not in inter.user.roles:
            raise Exception("You do not have permission to do this!")

        await inter.message.reply(content= "<@&917051613196193812> this pickup is looking for more players!")

    elif id == "Add Roles":
        roles = get_roles(inter.user, True)
        embed = discord.Embed(title= "Select roles you'd like to add.")
        
        class rolesView(ui.View):
            @ui.select(options= roles, placeholder= "Select roles you'd like to add.", max_values= len(roles))
            async def callback(self, roles_inter: discord.Interaction, selectMenu: discord.SelectMenu):
                roles_to_add = []

                for role in roles_inter.data["values"]:
                    role = inter.guild.get_role(int(role))
                    roles_to_add.append(role)

                await inter.delete_original_response()
                await inter.user.add_roles(*roles_to_add, reason= "Information channel - ADD")
                await roles_inter.response.send_message(content= "*Roles have been added.*", ephemeral= True)

        view = None

        if len(roles) == 0:
            embed.title = "You have all of the roles!"
        else:
            view = rolesView()

        await inter.response.send_message(embed= embed, view= view, ephemeral= True)
    
    elif id == "Remove Roles":
        roles = get_roles(inter.user, False)
        embed = discord.Embed(title= "Select roles you'd like to remove.")
        
        class rolesView(ui.View):
            @ui.select(options= roles, placeholder= "Select roles you'd like to remove.", max_values= len(roles))
            async def callback(self, roles_inter: discord.Interaction, selectMenu: discord.SelectMenu):
                roles_to_remove = []

                for role in roles_inter.data["values"]:
                    role = inter.guild.get_role(int(role))
                    roles_to_remove.append(role)

                await inter.delete_original_response()
                await inter.user.remove_roles(*roles_to_remove, reason= "Information channel - REMOVE")
                await roles_inter.response.send_message(content= "*Roles have been removed.*", ephemeral= True)

        view = None

        if len(roles) == 0:
            embed.title = "You do not have any roles!"
        else:
            view = rolesView()

        await inter.response.send_message(embed= embed, view= view, ephemeral= True)

@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    embed = discord.Embed(title="Error", description="There was an error when processing the command.", color=discord.Color.red())
    embed.add_field(name= "``Error Description``", value= "*"+str(error)+"*")

    await interaction.response.send_message(embed= embed, ephemeral=True)


'''@app_commands.guild_only()
class interest_sign_up(app_commands.Group, name= "interestform"):
    @app_commands.command()
    async def create(self, inter: discord.interactions.Interaction) -> None:
        await inter.response.send_modal(InterestForm())

    @app_commands.command()
    async def view(self, inter: discord.interactions.Interaction) -> None:
        pass

    @app_commands.command()
    async def edit(self, inter: discord.interactions.Interaction) -> None:
        pass'''

@tree.command()
async def positions(inter: discord.interactions.Interaction):
    embed = discord.Embed(title="Handball Positions", description="This is a list of officially recognized *Handball: The League* positions.", color=discord.Color.purple())
    embed.add_field(name= ":one: ``Striker``", value="Strikers focus on scoring the points. Strikers can usually be found on the opponent's side of the court.", inline= False)
    embed.add_field(name= ":two: ``Midfielder``", value= "Midfielders focus on moving the ball around and providing support to both defenders and strikers. Midfielders can usually be found near the middle of the court.", inline=False)
    embed.add_field(name= ":three: ``Defender``", value= "Defenders focus on stopping the opposing team's offense. Defender can usually be found on their own side of the court.", inline=False)
    embed.add_field(name= ":four: ``Goalkeeper``", value="Goalkeepers focus on saving shot attempts made by the opposing team. Goalkeepers can usually be found inside of the smaller ring circling the goal. A team can only have 1 GK at time.", inline=False)

    await inter.response.send_message(embed= embed, ephemeral= True)

@tree.command()
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

#@tree.command()
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
                    
                    try:
                        user: roblox.BaseUser = await roClient.get_user_by_username(robloxUsername)
                    except roblox.UserNotFound:
                        await interaction.response.send_message(content="*User was not found. Please restart using the ``/verify`` command.*")
                        await interaction.message.delete()
                        return

                    confirm = discord.Embed(title= "Is this you?")
                    confirm.add_field(name= "``Username``", value= user.name)
                    confirm.add_field(name= "``UserId``", value= user.id)

                    thumbnails = await roClient.thumbnails.get_user_avatar_thumbnails(
                        users= [user],
                        type= roblox.thumbnails.AvatarThumbnailType.headshot,
                        size= (100,100)
                    )

                    if len(thumbnails) > 0:
                        confirm.set_thumbnail(url= thumbnails[0].image_url)

                    class confirmView(ui.View):
                        @ui.button(label= "Yes", style=discord.ButtonStyle.green)
                        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                            async def checkGroup():
                                group = await roClient.get_group(10195697)
                                members = await group.get_members().flatten()
                                
                                inGroup = False

                                for member in members:
                                    if member.id == user.id:
                                        inGroup = True
                                        break

                                return inGroup

                            await interaction.message.delete()
                            await interaction.response.send_message("*I am checking if your account is in the HTL Roblox group...*")
                            if not await checkGroup():
                                await interaction.user.send("*It appears that you are not in the HTL group.\nJoin this group and then try again: {}*".format("https://www.roblox.com/groups/10195697/Handball-The-League#!/about"))
                            else:
                                try:
                                    databases["Player Data"]["Verification"].update_one({'discord': inter.user.id}, {'$set': {'roblox': user.id, 'confirmed': False, 'discord_username': inter.user.name}}, upsert=True)
                                except:
                                    await interaction.user.send(content="*There was an error during saving your information. Please restart using the ``/verify`` command.")
                                    return
                                    
                                await interaction.delete_original_response()
                                await interaction.user.send(content="**Your information has been saved, you are almost done!\n\nAll you have to do is join the following game and click \"Verify\"\nhttps://www.roblox.com/games/6732385646/Handball-The-Hub.**")
                            
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