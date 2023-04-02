import discord
from discord import app_commands, ui
from Modules.teamRoles import teamCheck
from settings import bot, htl_servers

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

@app_commands.guild_only()
class free_agency(app_commands.Group):
    @app_commands.command()
    @app_commands.checks.has_role("Membership")
    async def post(self, inter:discord.interactions.Interaction):
        if teamCheck(inter.user, bot.get_guild(htl_servers["League"]))[0]:
            raise Exception("You are already on a team!")

        await inter.response.send_modal(FA_Post())

bot.tree.add_command(free_agency())