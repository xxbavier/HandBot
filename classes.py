from typing import Any
import discord
from discord import ui

class InterestForm(ui.Modal, title= "Player Interest Form"):
    roblox = ui.TextInput(label='Roblox Username', style=discord.TextStyle.short)
    region = ui.TextInput(label='What region are you from?', style=discord.TextStyle.short)
    position = ui.TextInput(label= 'What position(s) do you play?', placeholder= 'Use ``/positions`` for a list of positions.', style=discord.TextStyle.paragraph)

class ReportScores(ui.Modal, title= "Submit Game Scores"):
    def __init__(self, *, title: str = ..., wk: int) -> None:
        super().__init__(title=title)
        self["week"] = wk
    
    #week = ui.TextInput(label= 'What week is this game for?', style=discord.TextStyle.short, placeholder='This MUST be a number.', max_length= 3)
    team_one = ui.TextInput(label= 'Please name Team 1.', style= discord.TextStyle.short)
    team_one_score = ui.TextInput(label= 'What was the score for Team 1?', style= discord.TextStyle.short, placeholder="This MUST be a number.", max_length= 3)
    team_two = ui.TextInput(label= 'Please name Team 2.', style= discord.TextStyle.short)
    team_two_score = ui.TextInput(label= 'What was the score for Team 2?', style= discord.TextStyle.short, placeholder="This MUST be a number.", max_length= 3)

    async def on_submit(self, inter: discord.interactions.Interaction):
        scores = {
            'team_one': int(self.team_one_score.value),
            'team_two': int(self.team_two_score.value)
        }

        embed = discord.Embed(title= "WEEK {} | {} vs {}".format(getattr(self, 'week'), self.team_one.value, self.team_two.value))
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

        embed = discord.Embed(title= "Game Scores Submitted!", description= "Here's a receipt of what you submitted:")
        embed.add_field(name= "``Week``", value= getattr(self, 'week'), inline=False)
        embed.add_field(name= "``Team 1 Name``", value= self.team_one.value, inline=False)
        embed.add_field(name= "``Team 1 Score``", value= self.team_one_score.value, inline=False)
        embed.add_field(name= "``Team 2 Name``", value= self.team_two.value, inline=False)
        embed.add_field(name= "``Team 2 Score``", value= self.team_two_score.value, inline=False)

        await inter.response.send_message(embed= embed, ephemeral=True)

        