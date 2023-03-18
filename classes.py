from typing import Any
import discord
from discord import ui

class InterestForm(ui.Modal, title= "Player Interest Form"):
    roblox = ui.TextInput(label='Roblox Username', style=discord.TextStyle.short)
    region = ui.TextInput(label='What region are you from?', style=discord.TextStyle.short)
    position = ui.TextInput(label= 'What position(s) do you play?', placeholder= 'Use ``/positions`` for a list of positions.', style=discord.TextStyle.paragraph)

class FA_Post(ui.Modal, title= "Free Agency Post"):
    positions = ui.TextInput(label= "What positions do you play?", placeholder="Use \"\positions\" to view a list of official positions.", style=discord.TextStyle.long)
    pros = ui.TextInput(label= "What are some of your pros?", style=discord.TextStyle.long)
    cons = ui.TextInput(label= "What are some of your cons?", style= discord.TextStyle.long)
    extra = ui.TextInput(label= "Anything else you'd like to say?", style=discord.TextStyle.long)

    async def on_submit(self, interaction: discord.Interaction, /) -> None:
        post = discord.Embed(title=interaction.user.name, description="A new free agency post has been made!", color= discord.Color.blurple())
        post.add_field(name= "``Positions``", value= self.positions.value, inline= False)
        post.add_field(name= "``Pros``", value= self.pros.value, inline= False)
        post.add_field(name= "``Cons``", value=self.cons.value, inline= False)
        post.add_field(name= "``Extra``", value= self.extra.value, inline= False)
        post.add_field(name= "``Contact``", value= "{} ({})".format(interaction.user.mention, interaction.user.name))

        await interaction.guild.get_channel(917102894522716230).send(embed= post)

        embed = discord.Embed(
            title= "Submitted",
            description= "Your free agency post has been successfully posted in <#917102894522716230>.",
            color= discord.Color.green()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)