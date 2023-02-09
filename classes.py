from typing import Any
import discord
from discord import ui

class InterestForm(ui.Modal, title= "Player Interest Form"):
    roblox = ui.TextInput(label='Roblox Username', style=discord.TextStyle.short)
    region = ui.TextInput(label='What region are you from?', style=discord.TextStyle.short)
    position = ui.TextInput(label= 'What position(s) do you play?', placeholder= 'Use ``/positions`` for a list of positions.', style=discord.TextStyle.paragraph)