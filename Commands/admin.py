import discord
from discord import app_commands, ui
from settings import bot

@app_commands.guild_only()
class admin(app_commands.Group):
    @app_commands.command()
    @app_commands.checks.has_any_role("Founder", "President")
    async def information(self, inter: discord.Interaction):
        embed = discord.Embed(title= "Handball: The League", description= "Welcome to *Handball: The League!*")
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/914661528593125387/1072928961329369158/htl.png?width=818&height=894")

        class informationView(ui.View):
            @ui.select(options=[
                discord.SelectOption(label= "Introduction", emoji= "👋", value= "Introduction"),
                discord.SelectOption(label= "Getting Started", emoji= "🔰", value= "Getting Started"),
                discord.SelectOption(label= "League Invite", emoji= "🌐", value= "League Invite"),
                discord.SelectOption(label= "Game", emoji= "🕹️", value= "Game"),
                discord.SelectOption(label= "Rulebook", emoji= "📜", value= "Rulebook"),
                discord.SelectOption(label= "Roles", emoji= "📒", value= "Roles"),
                discord.SelectOption(label= "Apply", emoji= "💎", value= "Applications"),
            ], custom_id= "Information", placeholder= "Select module you'd like to read.")
            async def callback():
                pass
        
        await inter.guild.get_channel(914661528593125387).send(embed= embed, view= informationView())
        await inter.response.send_message(content="*The information embed has been sent.*")\

bot.tree.add_command(admin())