import discord
from discord.ext import commands

transactions_enabled = True
transactions_channel_id = 1189408199871315988
#leaderboard_message_id = 1093693549968633906
team_cap = 15

htl_servers = {
    "League": 1232218908665057342
}

bot = commands.Bot(command_prefix= "?", intents=discord.Intents.all(), application_id= 885266060796899329)