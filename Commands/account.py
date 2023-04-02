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

client = Client()

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
                                "Handbowl Rings": {},
                                "Tournament Rings": {},
                                "Awards": {},
                                "All Pros": {},
                                "All Stars": {},
                                "Hall of Fame": False,
                            }
                        }

                        await bot.get_guild(htl_servers["League"]).get_member(inter.user.id).add_roles(bot.get_guild(htl_servers["League"]).get_role(910371139803553812))
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
        
        for key, medal in cursor["Medals"].items():
            if key != "Hall of Fame":
                embed.add_field(name= f"``{key}``", value= f"> {len(medal)}", inline= False)

        if cursor["Medals"]["Hall of Fame"]:
            hof = "> This player is in the Hall of Fame."
        else:
            hof = "> This player is not in the Hall of Fame."

        embed.add_field(name= "``Hall of Fame``", value= hof, inline= False)
                
        
        await inter.response.send_message(embed= embed)

        


bot.tree.add_command(account())