import discord
from discord import app_commands
from Modules.teamRoles import isTeamRole, coachRoles, coachCheck
from typing import List
from settings import bot

async def teams_autocomplete(inter: discord.Integration, current: str) -> List[app_commands.Choice[str]]:
    teams = []

    for role in inter.guild.roles:
        if isTeamRole(inter.guild.id, role.id):
            teams.append([role.name, str(role.id)])
    
    choices = []

    for teamList in teams:
        choices.append(app_commands.Choice(name=teamList[0], value=teamList[1]))

    return choices

@app_commands.guild_only()
class teams(app_commands.Group):
    @app_commands.command()
    @app_commands.checks.has_any_role("Founder", "President")
    @app_commands.autocomplete(team= teams_autocomplete)
    async def disband(self, inter: discord.Interaction, team: str):
        team: discord.Role = inter.guild.get_role(int(team))

        for member in team.members:
            await member.remove_roles(team, inter.guild.get_role(coachRoles["TO"]), inter.guild.get_role(coachRoles["GM"]))

            embed = discord.Embed(title= "``Team Disbanded``", description="Your team has been disbanded. You are now a Free Agent.", color= team.color)
            embed.add_field(name= "``Team Name``", value= team.name)

            await member.send(embed= embed)

        embed = discord.Embed(title= "Disbanded Team", color= team.color)
        embed.add_field("``Team``", value= team.name)

        await inter.response.send_message(embed= embed)

    @app_commands.command()
    @app_commands.autocomplete(team= teams_autocomplete)
    async def roster(self, inter: discord.Interaction, team: str, coaches: bool = False):
        team: discord.Role = inter.guild.get_role(int(team))

        for e in inter.guild.emojis:
            if team.name.find(e.name) > -1:
                break

        embed = discord.Embed(title= "{} {}".format(e, team.name), color= team.color)
        embed.set_footer(text= "Team Size: {}".format(len(team.members)))

        for member in team.members:
            if coachCheck(member, inter.guild) == 3:
                coachingPos = "``Team Owner``"
            elif coachCheck(member, inter.guild) == 2:
                coachingPos = "``General Manager``"
            else:
                if coaches:
                    continue

                coachingPos = "``Player``"

            embed.add_field(name= coachingPos, value= "{} ({})".format(member.mention, member.name))

        await inter.response.send_message(embed= embed, ephemeral= True)

bot.tree.add_command(teams())