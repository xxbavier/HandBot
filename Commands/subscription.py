from apscheduler.schedulers.asyncio import AsyncIOScheduler
import discord
from discord import app_commands, ui
from settings import bot
from Modules.database import databases
import time, math
import datetime

@app_commands.guild_only()
class subscription(app_commands.Group):
    @app_commands.command()
    @app_commands.checks.has_any_role("Silver Tier", "Gold Tier", "Diamond Tier")
    async def nickname(self, inter: discord.Interaction, target: discord.Member, nickname: str):
        cooldown = databases["Subscriptions"]["NicknameCooldown"].find_one({"DiscordId": inter.user.id})
        now = time.time()
        
        if cooldown and now - cooldown["SetTime"] < 60 * 60 * 24:
            # Not enough time has passed
            timedelta_obj = datetime.timedelta(seconds=round((cooldown["SetTime"] + 60 * 60 * 24) - now))
            embed = discord.Embed(title= "Cannot change nickname!")
            embed.description = "You have already changed someone's nickname in the past 24 hours!"
            embed.color = discord.Color.red()
            embed.add_field(name='Time Remaining', value= "{}".format(timedelta_obj))
            await inter.response.send_message(embed=embed)
            return
        
        await target.edit(nick=nickname)

        embed = discord.Embed(title= "Nickname changed!")
        embed.description = "You have changed {}'s nickname, they are now {}!".format(target.name, nickname)
        embed.color = discord.Color.green()
        await inter.response.send_message(embed=embed)
        
        if cooldown:
            databases["Player Data"]["Careers"].update_one({'DiscordId': inter.user.id}, {'$set': {"SetTime": math.floor(now)}})
        else:
            databases["Subscriptions"]["NicknameCooldown"].insert_one({
                'DiscordId': inter.user.id,
                'SetTime': math.floor(now)
            })

bot.tree.add_command(subscription())