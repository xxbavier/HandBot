import discord
from discord.ext import commands

transactions_enabled = False
transactions_channel_id = 917102767208816680

htl_servers = {
    "League": 909153380268650516,
    "Media": 928509118208180275,
    "Administration": 1020429868762144848
}

bot = commands.Bot(command_prefix= "?", intents=discord.Intents.all(), application_id= 885266060796899329)