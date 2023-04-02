import discord
from discord import app_commands, ui
import re, requests
from bs4 import BeautifulSoup
from urllib import response
from urllib.parse import urlparse
from settings import bot

@app_commands.guild_only()
class events(app_commands.Group):
    @app_commands.command()
    @app_commands.checks.has_role("Event Host")
    async def pickup(self, inter: discord.Interaction):
        class pickupMaker(ui.Modal):
            private_server_url = ui.TextInput(label= "Please enter your HBA Private Server link.", placeholder= "Paste Private Server link here.")
            extra = ui.TextInput(label= "Does this pickup have a description?", style= discord.TextStyle.long, required= False)

            async def on_submit(self, inter: discord.Interaction) -> None:
                embed = discord.Embed(title= "A Pickup Is Being Hosted!", color= discord.Colour.gold())
                embed.add_field(name= "``Host``", value= f"{inter.user.mention} ({inter.user.name})", inline=False)
                embed.set_author(name= inter.user.id)
                
                if self.extra.value:
                    embed.add_field(name= "``Description``", value= self.extra.value)

                pickupView = ui.View()
                
                domain = urlparse(self.private_server_url.value).netloc

                if domain != "www.roblox.com":
                    raise Exception("The URL must be a Roblox URL.")

                game_id = re.findall(r'\d+', self.private_server_url.value)[0]

                response = requests.get(f"https://www.roblox.com/games/{game_id}")

                soup = BeautifulSoup(response.text, 'html.parser')

                try:
                    img = soup.find("meta", property= "og:image")["content"]
                except Exception:
                    img = None

                if img:
                    embed.set_image(url = img)

                ps_button = ui.Button(label= "Click to Join", url= self.private_server_url.value)
                ping_for_more = ui.Button(label= "Ping Again", style= discord.ButtonStyle.green, custom_id= "Ping Again")
                delete = ui.Button(label= "Delete", style= discord.ButtonStyle.red, custom_id= "Delete Pickup")

                pickupView.add_item(ps_button)
                pickupView.add_item(ping_for_more)
                pickupView.add_item(delete)

                msg = await inter.guild.get_channel(917053987960782898).send(content= "<@&917051613196193812>", embed= embed, view= pickupView)
                await msg.delete(delay= 60 * 60)

                confirmationView = ui.View()
                confirmationView.add_item(ui.Button(label= "Go To Message", url= msg.jump_url))

                confirmation = discord.Embed(title= "Pickup Posted", description= "Your pickup has been posted.")

                await inter.response.send_message(embed= confirmation, view= confirmationView, ephemeral= True)

        await inter.response.send_modal(pickupMaker(title= "Pickup Maker"))

bot.tree.add_command(events())