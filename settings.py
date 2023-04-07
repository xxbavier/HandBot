import discord
from discord.ext import commands

transactions_enabled = True
transactions_channel_id = 917102767208816680
leaderboard_message_id = 1093693549968633906
team_cap = 15

htl_servers = {
    "League": 909153380268650516,
    "Media": 928509118208180275,
    "Administration": 1020429868762144848
}

bot = commands.Bot(command_prefix= "?", intents=discord.Intents.all(), application_id= 885266060796899329)