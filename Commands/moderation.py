import discord
from discord import app_commands
import datetime
from settings import bot

@app_commands.guild_only()
class moderation(app_commands.Group):
    @app_commands.command()
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self, inter: discord.Interaction, count: int, member: discord.Member = None):
        count = min(count, 100)
        
        if member:
            def check(msg):
                return msg.author == member

            msgs = await inter.channel.purge(limit=count, check=check)
        else:
            msgs = await inter.channel.purge(limit=count)

        embed = discord.Embed(title= "Purged Channel", color= discord.Color.red())
        embed.add_field("``# of Messages Deleted``", value= str(len(msgs)))
        embed.set_footer(icon_url=inter.user.avatar.url, text= "{} ({})".format(inter.user.name, inter.user.id))

        await inter.response.send_message(embed=embed, delete_after=2)
        embed.add_field("``Channel``", value= f"<#{inter.channel.id}>")

        await inter.guild.get_channel(1244849165612093501).send(embed= embed)


    @app_commands.command()
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(self, inter: discord.interactions.Interaction, member: discord.Member, reason: str, minutes: int = 30, hours: int = 0, days: int = 0, weeks: int = 0):
        if inter.user.top_role.position <= member.top_role.position:
            raise Exception("The member you tried muting has a higher role than you.")

        x = datetime.timedelta(
            minutes= minutes,
            hours= hours,
            days= days,
            weeks= weeks
        )

        await member.timeout(x)

        embed = discord.Embed(title= "Mute", color= discord.Color.red())
        embed.set_author(name= "Subject: {} ({})".format(member.name, member.id), icon_url= member.avatar.url)
        embed.add_field(name= "``Reason``", value= reason)
        embed.add_field(name= "``Length``", value= str(x))
        embed.set_footer(text= "Moderator: {} ({})".format(inter.user.name, inter.user.id), icon_url= inter.user.avatar.url)

        await inter.response.send_message(embed= embed)
        await member.send(embed= embed)
        await inter.guild.get_channel(1244849165612093501).send(embed= embed)
    
    @app_commands.command()
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, inter: discord.interactions.Interaction, member: discord.Member, reason: str):
        if inter.user.top_role.position <= member.top_role.position:
            raise Exception("The member you tried unmuting has a higher role than you.")

        if not member.is_timed_out():
            raise Exception("Member is not muted.")

        await member.timeout(None)

        embed = discord.Embed(title= "Unmute", color= discord.Color.green())
        embed.set_author(name= "Subject: {} ({})".format(member.name, member.id), icon_url= member.avatar.url)
        embed.add_field(name= "``Reason``", value= reason)
        embed.set_footer(text= "Moderator: {} ({})".format(inter.user.name, inter.user.id), icon_url= inter.user.avatar.url)

        await inter.response.send_message(embed= embed)
        await member.send(embed= embed)
        await inter.guild.get_channel(1244849165612093501).send(embed= embed)

    @app_commands.command()
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, inter: discord.interactions.Interaction, member: discord.Member, reason: str):
        if inter.user.top_role.position <= member.top_role.position:
            raise Exception("The member you tried kicking has a higher role than you.")

        await member.kick(reason=reason)

        embed = discord.Embed(title= "Kick", color= discord.Color.red())
        embed.set_author(name= "Subject: {} ({})".format(member.name, member.id), icon_url= member.avatar.url)
        embed.add_field(name= "``Reason``", value= reason)
        embed.set_footer(text= "Moderator: {} ({})".format(inter.user.name, inter.user.id), icon_url= inter.user.avatar.url)

        await inter.response.send_message(embed= embed)
        await member.send(embed= embed)
        await inter.guild.get_channel(1244849165612093501).send(embed= embed)

    @app_commands.command()
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, inter: discord.interactions.Interaction, member: discord.Member, reason: str):
        if inter.user.top_role.position <= member.top_role.position:
            raise Exception("The member you tried banning has a higher role than you.")
            
        await member.ban(reason=reason)

        embed = discord.Embed(title= "Ban", color= discord.Color.red())
        embed.set_author(name= "Subject: {} ({})".format(member.name, member.id), icon_url= member.avatar.url)
        embed.add_field(name= "``Reason``", value= reason)
        embed.set_footer(text= "Moderator: {} ({})".format(inter.user.name, inter.user.id), icon_url= inter.user.avatar.url)

        await inter.response.send_message(embed= embed)
        await member.send(embed= embed)
        await inter.guild.get_channel(1244849165612093501).send(embed= embed)

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def unban(self, inter: discord.interactions.Interaction, user: discord.User = None, member_id: str = None):
        user = user or bot.get_user(int(member_id))

        try:
            await inter.guild.unban(user= user)
        except discord.NotFound:
            raise Exception("User was not found in the ban list.")
        except Exception:
            raise Exception("Unknown error occurred.")


        embed = discord.Embed(title= "Unban", color= discord.Color.green())
        embed.set_author(name= "Subject: {} ({})".format(user.name, user.id), icon_url= user.avatar.url)
        embed.set_footer(text= "Moderator: {} ({})".format(inter.user.name, inter.user.id), icon_url= inter.user.avatar.url)

        await inter.response.send_message(embed= embed)
        await inter.guild.get_channel(1244849165612093501).send(embed= embed)

bot.tree.add_command(moderation())