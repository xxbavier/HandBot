from apscheduler.schedulers.asyncio import AsyncIOScheduler
import discord
from discord import app_commands, ui
from settings import bot

@bot.tree.command()
async def subscriber(inter: discord.Interaction):
    pass