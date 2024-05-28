import discord
from discord import app_commands, ui
from settings import bot, htl_servers
from Modules.database import databases
from Modules.elo_system import new_rating, get_estimated_score, get_team_average
import roblox
import json
from Commands.teams import teams_autocomplete
from Modules.teamRoles import isTeamRole, getTeamAccounts
from Modules.RobloxCloud import DataStores
import time

DataStoreApi = DataStores()

roclient = roblox.Client()

def get_game(key) -> list:
    data = DataStoreApi.get_entry("HTL Stats", key)
    data = json.loads(data.json())
    return data

@app_commands.guild_only()
class admin(app_commands.Group):
    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def information(self, inter: discord.Interaction):
        embed = discord.Embed(title= "National Handball Association", description= "Welcome to the *National Handball Association*.")
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1207149176643657758/1208561490400116756/NHA.png?ex=65e3bb99&is=65d14699&hm=c033007fd5d3da8680749b8c00e7d986b751cf1fd114da7401bfe4b4b06987b7&=&format=webp&quality=lossless&width=700&height=700")

        informationView = ui.View()
        
        select = ui.Select(options=[
                discord.SelectOption(label= "Introduction", emoji= "👋", value= "Introduction"),
                discord.SelectOption(label= "Getting Started", emoji= "🔰", value= "Getting Started"),
                discord.SelectOption(label= "League Socials", emoji= "🌐", value= "League Socials"),
                discord.SelectOption(label= "Game", emoji= "🕹️", value= "Game"),
                discord.SelectOption(label= "Rulebook", emoji= "📜", value= "Rulebook"),
                discord.SelectOption(label= "Roles", emoji= "📒", value= "Roles"),
                discord.SelectOption(label= "Apply", emoji= "💎", value= "Applications"),
            ], custom_id= "Information", placeholder= "Select module you'd like to read.")

        informationView.add_item(select)

        await inter.channel.send(embed= embed, view= informationView)
        await inter.response.send_message(content="*The information embed has been sent.*", ephemeral= True)

    @app_commands.command()
    @app_commands.checks.has_permissions(manage_roles=True)
    async def role(self, inter: discord.Interaction, member: discord.Member, role: discord.Role):
        if role in member.roles:
            # Member already has the role, remove it
            await member.remove_roles(role, reason= "Removed by {}.".format(inter.user.name))

            embed = discord.Embed()
            embed.title = "Removed Role"
            embed.description = "``{}`` role has been removed from ``{}``.".format(role.name, member.name)
        else:
            # Member doesn't have the role, assign it
            await member.add_roles(role, reason= "Added by {}.".format(inter.user.name))

            embed = discord.Embed()
            embed.title = "Added Role"
            embed.description = "``{}`` role has been added to ``{}``.".format(role.name, member.name)
        
        await inter.response.send_message(embed= embed)


@bot.event
async def on_interaction(inter: discord.Interaction):
    data = inter.data

    try:
        id = data["custom_id"]
        
        if data["component_type"] != 2:
            values = data["values"]
    except Exception:
        return

    
    if id == "Information":
        embed = discord.Embed(title= values[0])
        view = None

        if values[0] == "Introduction":
            embed.description = "*Welcome to the National Handball Association. NHA is a NA-based league that was established in December of 2023.*\n\n**This channel is where you can find information about the league.**"

            view = ui.View()

            view.add_item(ui.Button(label= "Handball Positions", custom_id= "Positions", style= discord.ButtonStyle.blurple))

        elif values[0] == "Getting Started":
            embed.description = "*Upon joining the league, there are a few ways for new players to involve themselves in the league.*"

            class gettingStarted(ui.View):
                @ui.select(options=[
                    discord.SelectOption(label= "Pickups", emoji="🥅", value = "Pickups"),
                    discord.SelectOption(label= "Free Agency", emoji="🔰", value = "Free Agency"),
                    discord.SelectOption(label= "Chat", emoji="💬", value = "Chat"),
                ], placeholder= "Find ways to get started.", custom_id= "Getting Started")
                async def callback():
                    pass

            view = gettingStarted()
                
        elif values[0] == "League Socials":
            invite = await inter.channel.create_invite(
                reason= "Information channel",
                max_age=0,
                max_uses=0,
                unique=False
            )

            embed.add_field(name= "``Permanent Invite``", value= invite.url, inline= False)
            
            vanity = inter.guild.vanity_url

            if not vanity:
                vanity = "NHA does not have a vanity invite at the moment."

            embed.add_field(name= "``Vanity Invite``", value= vanity, inline= False)

            view = ui.View()

            youtube = ui.Button(label= "YouTube Page", url= "https://www.youtube.com/@HandballTheLeague")
            group = ui.Button(label= "League Group Page", url= "https://www.roblox.com/groups/10195697/Handball-The-League")

            view.add_item(youtube)
            view.add_item(group)

        elif values[0] == "Game":
            embed.description = "Click the buttons to access the Game sites."

            view = ui.View()

            game = ui.Button(label= "Game Page", url= "https://www.roblox.com/games/5498056786", style= discord.ButtonStyle.gray)
            game_discord = ui.Button(label= "Game Discord", url= "https://discord.gg/VUhYsAtKPU", style= discord.ButtonStyle.gray)
            
            view.add_item(game)
            view.add_item(game_discord)

        elif values[0] == "Rulebook":
            embed.description = "Click the button to access the rulebook."

            view = ui.View()
            
            rulebook = ui.Button(label= "Rulebook", url= "https://docs.google.com/document/d/1blgWUD2JOHCZrDZ_VmUtJwNbDsDhOW9H-1YslFCPBjg/edit#heading=h.n29msmna3upk")

            view.add_item(rulebook)

        elif values[0] == "Roles":
            view = ui.View()

            roles = ui.Button(custom_id= "Roles Channel", url= "https://discord.com/channels/1189116739649290270/1189639835263193130")

            view.add_item(roles)
        
        elif values[0] == "Applications":
            embed.description = "*This module is not yet finished.*"

            #@ui.select()
        
        await inter.response.send_message(embed= embed, ephemeral= True, view= view)
    
    elif id == "Getting Started":
        embed = discord.Embed(title = values[0])
        view = None

        if values[0] == "Pickups":
            embed.description = "**Pickup games are mock games ran by the community.**\n\n> *Pickups are a great way to get yourself involved in HTL and to get others to notice your skill.*"
        elif values[0] == "Free Agency":
            embed.description = "**Teams are often looking for new players for their rosters and like to scout new players.**\n\n> *You can get noticed by posting a Free Agency advertisement in <#1093676364504256612> or by responding to posts made by Team Coaches in <#1093701368902066236>.*"
        elif values[0] == "Chat":
            embed.description = "**Talking to other members in the league and forming connections is a good way to get involved in the league.**\n\n> *Some teams tend to tryout/recruit members that are active in the community; in addition, forming connections is a good way to form a team if a member is interested in owning a team.*"

        await inter.response.send_message(embed= embed, ephemeral= True, view=view)

    elif id == "Positions":
        embed = discord.Embed(title="Handball Positions", description="This is a list of officially recognized positions.", color=discord.Color.purple())
        embed.add_field(name= ":one: ``Striker``", value="Strikers focus on scoring the points. Strikers can usually be found on the opponent's side of the court.", inline= False)
        embed.add_field(name= ":two: ``Midfielder``", value= "Midfielders focus on moving the ball around and providing support to both defenders and strikers. Midfielders can usually be found near the middle of the court.", inline=False)
        embed.add_field(name= ":three: ``Defender``", value= "Defenders focus on stopping the opposing team's offense. Defender can usually be found on their own side of the court.", inline=False)
        embed.add_field(name= ":four: ``Goalkeeper``", value="Goalkeepers focus on saving shot attempts made by the opposing team. Goalkeepers can usually be found inside of the smaller ring circling the goal. A team can only have 1 GK at time.", inline=False)

        await inter.response.send_message(embed= embed, ephemeral= True)


bot.tree.add_command(admin())