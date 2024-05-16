import discord, pprint, requests, random, asyncio
from discord import app_commands, ui
from Modules import rover, database
from settings import bot, htl_servers

@app_commands.guild_only()
class admin(app_commands.Group):
    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def create_signup(self, inter: discord.Interaction, series: str):
        embed = discord.Embed()
        embed.title = "Player Sign-Up"
        embed.description = "Press the button below if you are interested in playing this season."
        
        view = ui.View()

        signup_button = ui.Button(label="Sign Up for Series", style= discord.ButtonStyle.blurple, custom_id="Sign Up,{}".format(series))

        view.add_item(signup_button)

        await inter.channel.send(embed= embed, view= view)
        await inter.response.send_message("*Sign up embed has been created in this channel.*", ephemeral= True)

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def generate_teams(self, inter: discord.Interaction, series: str, size: int):
        await inter.response.defer(ephemeral= False, thinking= True)

        guild = bot.get_guild(htl_servers["League"])
        category = discord.utils.get(bot.get_guild(htl_servers["League"]).categories, id= 1236742676666388531)
        top_role = 1236763852259983460
        bottom_role = 1236763921520787536

        for channel in category.channels:
            await channel.delete()

        cursor = database.databases["Current Sign Up"][series].find()
        data = list(cursor)
                
        team_count = len(data)//min(size, len(data))
        teams = {}

        for x in range(team_count):
            team = []

            for y in range(min(size, len(data))):
                index = random.choice(list(range(0, len(data))))
                player = data[index]
                team.append(player)

            teams["Team {}".format(x)] = team

        embeds = []

        top_role_pos = bot.get_guild(htl_servers["League"]).get_role(top_role).position

        for name, value in teams.items():
            embed = discord.Embed()
            embed.title = name

            color = discord.Colour.random()
            
            role = await guild.create_role(
                name= name,
                color= color,
                reason= "Team generation.",
                hoist= True
            )

            await guild.create_text_channel(
                name=name,
                reason= "Team generation.",
                category= category,
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    role: discord.PermissionOverwrite(read_messages=True)
                }
            )

            string_list = []

            for member in value:
                user = bot.get_user(member["DiscordId"])
                string_list.append("{} {}".format(user.name, user.mention))

                await guild.get_member(user.id).add_roles(role)

            embed.color = color
            embed.description = "\n".join(string_list)

            embeds.append(embed)

        await bot.get_guild(htl_servers["League"]).get_role(bottom_role).edit(position= top_role_pos - len(teams))
        await inter.edit_original_response(embeds= embeds)

@bot.event
async def on_interaction(inter: discord.Interaction):
    if inter.data.get("custom_id"):
        inter_data = inter.data["custom_id"].split(",")
        if inter_data[0] == "Sign Up":
            series = inter_data[1]

            data = rover.get_Roblox(inter.guild.id, inter.user.id)

            try:
                robloxId = data['robloxId']
            except KeyError:
                embed = discord.Embed(title="Error", description="There was an error when processing the command.", color=discord.Color.red())
                embed.add_field(name= "``Error Description``", value= "*"+str("You are not verified through RoVer.")+"*")

                await inter.response.send_message(embed= embed, ephemeral=True)
                return

            result = database.databases["Current Sign Up"][series].find_one({"DiscordId": inter.user.id})
            result = False

            if not result:
                database.databases["Current Sign Up"][series].insert_one({"DiscordId": inter.user.id, "RobloxId": robloxId})

                embed = discord.Embed()
                embed.title = "Success!"
                embed.description = "*You have successfully signed up for the {} Series.*".format(series)
                embed.color = discord.Colour.green()
            else:
                embed = discord.Embed()
                embed.title = "Error"
                embed.description = "*You have already signed up for the {} Series.*".format(series)
                embed.color = discord.Colour.red()

            await inter.response.send_message(embed= embed, ephemeral= True)

bot.tree.add_command(admin())