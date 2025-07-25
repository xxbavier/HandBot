import discord
from discord.ext import commands
from discord import client

class MemberSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
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
        embed.set_thumbnail(url=member.guild.icon)
        embed.color = discord.Color.orange()

        await member.send(content="https://discord.gg/vPz6zkATev", embed= embed)

        '''roles = [
            1209253356829151272,
            1192374103609454683,
            1192374441934602340,
            1189126244743262278,
            1241443258500907139,
            1192373637173477437
        ]'''

        #await member.add_roles(*[member.guild.get_role(role) for role in roles])
        await member.guild.get_channel(1375162934250049647).send(content="<:Green:1398092411842072708> | **{} has joined the server.** ``Members: {}``".format(member.mention, member.guild.member_count))

    @commands.Cog.listener()
    async def on_raw_member_remove(self, member: discord.RawMemberRemoveEvent):
        await self.bot.get_guild(member.guild_id).get_channel(1189275682639990924).send(content="<:Red:1398092453416009912> | *{}#{} has left the server.*".format(member.user.name, member.user.discriminator))
    

async def setup(bot: commands.Bot):
    await bot.add_cog(MemberSetup(bot=bot))