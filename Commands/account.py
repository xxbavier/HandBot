from typing import Optional
import discord
from discord import app_commands, ui
from settings import bot, htl_servers
import requests
import random
import roblox
from roblox import Client, users, thumbnails
from Modules.elo_system import starting_elo
from Modules.database import databases
from typing import List

client = Client()

async def awards_autocomplete(inter: discord.Integration, current: str) -> List[app_commands.Choice[str]]:
    choices = []

    awards = {
        "Handbowl Rings": {
            "Handbowl Champions"
        },
        "Awards": {
            "Striker of the Year",
            "Defender of the Year",
            "Passer of the Year",
            "Goalkeeper of the Year",
            "Most Valuable Player"
        },
        "All Pros": [f"{o} Overall" for o in list(range(90, 100))],
        "All Stars": {
            "All-Star Team"
        },
        "Hall of Fame": {
            "Hall of Fame"
        }
    }

    for category, data in awards.items():
        for award in data:
            choices.append(app_commands.Choice(name= award, value= ",".join([category, award])))

    return choices

async def handle_interaction(inter: discord.Interaction):
    id = inter.data["custom_id"].split(" ")

    if id[0] == "account":
        if id[1] == "create":
            if id[2] == "1":
                class getRoblox(ui.Modal, title= "HTL Account Creation"):
                    roblox = ui.TextInput(label= "What is your Roblox username?", style= discord.TextStyle.short, custom_id="account create 2")

                    async def on_submit(self, interaction: discord.Interaction, /) -> None:
                        embed = discord.Embed(title= "HTL Account Creation", color= discord.Color.yellow(), description= "Is this you?")
                        embed.add_field(name= "``Roblox Username``", value= self.roblox.value)

                        options = ui.View()
                        options.add_item(ui.Button(label= "Yes", style= discord.ButtonStyle.green, custom_id= "account create 2"))
                        options.add_item(ui.Button(label= "No", style= discord.ButtonStyle.red, custom_id= "account create 1"))

                        await interaction.response.defer()
                        await inter.message.edit(embed= embed, view= options)                        

                await inter.response.send_modal(getRoblox())

            elif id[2] == "2":
                word_site = "https://www.mit.edu/~ecprice/wordlist.10000"

                response = requests.get(word_site)
                WORDS = response.text.splitlines()

                words = random.choices(WORDS, k= 5)
                words = ", ".join(words)

                embed = discord.Embed(title= "HTL Account Creation", description= f"Please set your Roblox About Me to the following words. If the words get tagged, click the regenerate words button and use the new set of words.", color= discord.Color.yellow())

                for field in inter.message.embeds[0].fields:
                    if field.name == "``Roblox Username``":
                        robloxUsername = field.value
                        break
                
                embed.add_field(name= "``Words``", value= words, inline= False)

                embed.add_field(name= "``Roblox Username``", value= robloxUsername, inline= False)

                actions = ui.View()
                actions.add_item(ui.Button(label= "Done", style= discord.ButtonStyle.green, custom_id= "account create confirm"))
                actions.add_item(ui.Button(label= "Regenerate Words", style= discord.ButtonStyle.blurple, custom_id= "account create 2"))

                await inter.response.defer()
                await inter.message.edit(embed= embed, view= actions)

            elif id[2] == "confirm":
                for field in inter.message.embeds[0].fields:
                    if field.name == "``Words``":
                        words = field.value

                    elif field.name == "``Roblox Username``":
                        username = field.value

                try:
                    user: users.User = await client.get_user_by_username(username= username, exclude_banned_users= True, expand= True)

                    robloxAccTaken = False

                    try:
                        cursor = databases['Player Data']["Careers"].find_one({'RobloxId': user.id})

                        if cursor:
                            robloxAccTaken = True
                    except:
                        robloxAccTaken = False

                    if robloxAccTaken:
                        raise Exception("This account has already been taken.")

                    if user.description == words:
                        account = {
                            "DiscordId": inter.user.id,
                            "RobloxId": user.id,
                            "Elo": starting_elo,
                            "Medals": {
                                "Handbowl Rings": [],
                                "Tournament Rings": [],
                                "Awards": [],
                                "All Pros": [],
                                "All Stars": [],
                                "Hall of Fame": None,
                            }
                        }

                        await bot.get_guild(htl_servers["League"]).get_member(inter.user.id).add_roles(bot.get_guild(htl_servers["League"]).get_role(910371139803553812))
                        await bot.get_channel(1070807124537507850).send(f"**{inter.user.mention}** ({inter.user.id}) has created an HTL Account using the following Roblox Account.\nhttps://www.roblox.com/users/{user.id}/profile")
                        databases["Player Data"]["Careers"].insert_one(account)
                        success = discord.Embed(title= "HTL Account Creation", description= "Congratulations! Your HTL Account has been officially created.", color= discord.Color.green())
                        await inter.message.edit(embed= success, view= None)
                    else:
                        raise Exception("The description was not set to the words provided.")

                except Exception as e:
                    embed = discord.Embed(title= "HTL Account Creation", description= str(e), color= discord.Color.red())

                    retry = ui.View()
                    retry.add_item(ui.Button(label= "Restart?", style= discord.ButtonStyle.green, custom_id= "account create 1"))

                    await inter.message.edit(embed= embed, view= retry)

                await inter.response.defer()


@app_commands.guild_only()
class account(app_commands.Group):
    @app_commands.command()
    @app_commands.checks.has_role(927074131227324446)
    async def create(self, inter: discord.Interaction):
        hasAccount = False

        try:
            cursor = databases['Player Data']["Careers"].find_one({'DiscordId': inter.user.id})

            if cursor:
                hasAccount = True
        except Exception:
            pass

        embed = discord.Embed(title= "HTL Account Creation", color= discord.Color.yellow())
        goToDM = None

        if hasAccount:
            embed.description = "You already have an HTL account!"
        else:
            embed.description = "Please click the button or check your DMs to continue."

            creation_embed = discord.Embed(title= "HTL Account Creation", description= "Welcome to the HTL Account creation! Please click the button to start.")
            creation_view = ui.View()
            creation_view.add_item(ui.Button(label= "Start", style= discord.ButtonStyle.green, custom_id= "account create 1"))

            msg = await inter.user.send(embed= creation_embed, view= creation_view)

            goToDM = ui.View()
            goToDM.add_item(ui.Button(label= "Go To DMs", url= msg.jump_url))     

        await inter.response.send_message(embed= embed, view= goToDM, ephemeral= True)

    @app_commands.command()
    async def view(self, inter: discord.Interaction, member: discord.Member):
        hasAccount = False

        try:
            cursor = databases['Player Data']["Careers"].find_one({'DiscordId': member.id})

            if cursor:
                hasAccount = True
        except Exception:
            hasAccount = False

        if not hasAccount:
            raise Exception("This user does not have an HTL Account!")
        
        robloxInfo = await client.get_user(cursor["RobloxId"])
        thumbnail = await client.thumbnails.get_user_avatar_thumbnails(users= [robloxInfo], type= thumbnails.AvatarThumbnailType.headshot, size= "100x100")
        thumbnail = thumbnail[0]

        embed = discord.Embed(title= f"{member.name}'s Account", color= member.color)
        embed.set_thumbnail(url= thumbnail.image_url)
        embed.add_field(name= "``Roblox Account``", value= f"{robloxInfo.display_name} (@{robloxInfo.name})\n{robloxInfo.id}", inline= False)
        embed.add_field(name= "``Elo``", value= cursor["Elo"], inline= False)
        
        '''for key, medal in cursor["Medals"].items():
            if key != "Hall of Fame":
                embed.add_field(name= f"``{key}``", value= f"> {len(medal)}", inline= False)'''

        hof_status = cursor["Medals"]["Hall of Fame"]

        if hof_status:
            hof = f"> {hof_status}"
        else:
            hof = "> This player is not in the Hall of Fame."

        embed.add_field(name= "``Hall of Fame``", value= hof, inline= False)

        options = [discord.SelectOption(label= category) for category in cursor["Medals"] if category != "Hall of Fame"]
        options.insert(0, discord.SelectOption(label= "Main Page"))

        class view(ui.View):
            @ui.select(options= options, placeholder= "Select an option to view this player's data.")
            async def callback(self, inter: discord.Interaction, selected: discord.SelectMenu):
                embed = discord.Embed(title= f"{member.name}'s Account", color= member.color)
                embed.set_thumbnail(url= thumbnail.image_url)

                category = inter.data["values"][0]

                if category == "Main Page":
                    embed.add_field(name= "``Roblox Account``", value= f"{robloxInfo.display_name} (@{robloxInfo.name})\n{robloxInfo.id}", inline= False)
                    embed.add_field(name= "``Elo``", value= cursor["Elo"], inline= False)

                    hof_status = cursor["Medals"]["Hall of Fame"]

                    if hof_status:
                        hof = f"> {hof_status}"
                    else:
                        hof = "> This player is not in the Hall of Fame."

                    embed.add_field(name= "``Hall of Fame``", value= hof, inline= False)

                else:
                    medal_count = len(cursor["Medals"][category])

                    if medal_count > 0:
                        embed.add_field(name= f"``{category}``", value= "> " + "\n> ".join(cursor["Medals"][category]))
                    else:
                        embed.add_field(name= f"``{category}``", value= "> No data recorded!")

                    embed.set_footer(text= f"{medal_count} medals")

                    embed.description = f"Here is the data this player has on record for the ``{category}`` category."

                await inter.message.edit(embed= embed)
                await inter.response.defer()

        await inter.response.send_message(embed= embed, view= view())
    
    @app_commands.command()
    @app_commands.autocomplete(award = awards_autocomplete)
    @app_commands.checks.has_any_role("Founder", "President", "Director")
    async def award(self, inter: discord.Interaction, htl_version: int, season: int, award: str, target_member: discord.Member= None, target_role: discord.Role= None, all_star_team_name: str= None):
        award = award.split(",")
        category = award[0]
        award = award[1]

        award_name = f"V{htl_version} S{season} {award}"

        if award == "All-Star Team":
            if not target_member:
                raise Exception("The **target_member** field must be filled when awarding this award.")
            
            if all_star_team_name:
                award += f" {all_star_team_name}"
            else:
                raise Exception("The All-Star Team Name field can not be left empty when assigning All-Star Awards.")
            
            target = target_member
        elif category == "Handbowl Rings":
            if not target_role:
                raise Exception("The **target_role** field must be filled when awarding this award.")
            
            target = target_role
        else:
            if not target_member:
                raise Exception("The **target_member** field must be filled when awarding this award.")
            
            target = target_member

        embed = discord.Embed(title= "Awards", description= "Are you sure you want to award this award?", color= discord.Color.yellow())
        embed.add_field(name= "``Target``", value= target.mention, inline= False)
        embed.add_field(name= "``Award``", value= award_name)

        awardConfirm = ui.View()

        class apply(ui.Button):
            async def callback(self, interaction: discord.Interaction):
                awarded_string = "> "

                def awardMember(member: discord.Member, award: str):
                    cursor = databases['Player Data']["Careers"].find_one({'DiscordId': member.id})

                    if cursor:
                        medals = cursor["Medals"]

                        if category == "Hall of Fame":
                            medals[category] = award
                        else:
                            if type(medals[category]) != list:
                                medals[category] = []
                            
                            if award in medals[category]:
                                return False

                            medals[category].append(award)

                        databases["Player Data"]["Careers"].update_one({'DiscordId': member.id}, {'$set': {"Medals": medals}})

                        return True
                    else:
                        return False

                if target == target_member:
                    if awardMember(target, award_name):
                        awarded_string += target.mention

                
                elif target == target_role:
                    listOfPlayers = []

                    for member in target.members:
                        if awardMember(member, award_name):
                            listOfPlayers.append(member.mention)
                    
                    awarded_string += "\n> ".join(listOfPlayers)

                embed = discord.Embed(title= "Awarded Player(s)", description= "The following award was given to the following player(s).", color= discord.Color.green())
                embed.add_field(name= "``Award``", value= award_name, inline= False)
                embed.add_field(name= "``Player(s)``", value= awarded_string, inline= False)
                embed.set_author(name= inter.user.name, icon_url= inter.user.avatar.url)
                
                await interaction.response.send_message(embed= embed)
                await bot.get_channel(1092229921839005787).send(embed= embed)

        awardConfirm.add_item(apply(label= "Apply", style= discord.ButtonStyle.green))

        await inter.response.send_message(embed=embed, view= awardConfirm, ephemeral= True)

        


bot.tree.add_command(account())