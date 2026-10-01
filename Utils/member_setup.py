import logging

import discord
from discord.ext import commands

from settings import WELCOME_INVITE

logger = logging.getLogger(__name__)


class MemberSetup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def send_member_log(self, guild: discord.Guild, content: str) -> None:
        channel_id = self.bot.settings.member_log_channel_id
        channel = guild.get_channel(channel_id)
        if channel is None:
            logger.warning(
                "Member log channel %s is unavailable in guild %s", channel_id, guild.id
            )
            return
        try:
            await channel.send(content=content)
        except discord.HTTPException:
            logger.warning("Could not send member log in guild %s", guild.id, exc_info=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        embed = discord.Embed()
        embed.title = "Welcome to *Handball: The League*."
        embed.description = """Welcome to HTL, a league inspired by olympic handball!"""
        embed.add_field(name="``What is Handball?``", value= """Handball is an olympic sport that is best described as a mixture of soccer and basketball.
                        
This server is a competitive league for a game on Roblox based on Olympic Handball--but with a few twists.""", inline= False)
        embed.add_field(name="``Want to try the game out?``", value= """In HTL, there are 2 Roblox games that are most relevant to the league.
                        
There's [Handball 2 (HB2)]({}) and [Handball Association 1.16 (HBA 1.16)]({}).
                        
__HB2 is the game that is currently used for the league.__""".format(
            "https://www.roblox.com/games/5498056786/Handball-2",
            "https://www.roblox.com/games/7521555382/HBA-1-16"
                        ), inline= False)
        embed.add_field(name="``How do you join a team?``", value="""In HTL, Team Owners and General Managers tend to sign people they know.

That being said, here's a few suggestions that can help get you involved:
1. Play pickups and get your name known by performing well.
2. Talk in <#1375158754529513484> and make friends.
3. Use <#1380285480264007892> to market your skills so that Team Coaches can see them.""", inline= False)
        embed.add_field(name= "``Want to become a Team Owner?``", value= "You can become a Team Owner by filling in [this form](https://forms.gle/o56a5dyqYtSFu77m6).", inline=False)
        if member.guild.icon is not None:
            embed.set_thumbnail(url=member.guild.icon.url)
        embed.color = discord.Color.orange()

        try:
            await member.send(content=WELCOME_INVITE, embed=embed)
        except discord.HTTPException:
            logger.warning("Could not send welcome DM to member %s", member.id, exc_info=True)

        await self.send_member_log(
            member.guild,
            content=(
                "<:Green:1398092411842072708> | **{} has joined the server.** "
                "``Members: {}``"
            ).format(member.mention, member.guild.member_count),
        )

    @commands.Cog.listener()
    async def on_raw_member_remove(self, member: discord.RawMemberRemoveEvent) -> None:
        guild = self.bot.get_guild(member.guild_id)
        if guild is None:
            logger.warning("Guild %s is unavailable for a member leave event", member.guild_id)
            return
        await self.send_member_log(
            guild,
            content="<:Red:1398092453416009912> | *{} has left the server.*".format(
                member.user.name
            ),
        )

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MemberSetup(bot=bot))
