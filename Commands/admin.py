import discord
from discord import app_commands, ui
from settings import bot, htl_servers, leaderboard_message_id
from Modules.database import databases
from Modules.elo_system import new_rating, get_estimated_score, get_team_average
import roblox
import json
from Commands.teams import teams_autocomplete
from Modules.teamRoles import isTeamRole, getTeamAccounts
from Modules.RobloxCloud import DataStores
import time

DataStoreApi = DataStores()

roclient = roblox.Client()

def get_game(key) -> list:
    data = DataStoreApi.get_entry("HTL Stats", key)
    data = json.loads(data.json())
    return data

@app_commands.guild_only()
class admin(app_commands.Group):
    @app_commands.command()
    @app_commands.checks.has_any_role("Founder", "President")
    async def information(self, inter: discord.Interaction):
        embed = discord.Embed(title= "Handball: The League", description= "Welcome to *Handball: The League!*")
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/914661528593125387/1072928961329369158/htl.png?width=818&height=894")

        class informationView(ui.View):
            @ui.select(options=[
                discord.SelectOption(label= "Introduction", emoji= "👋", value= "Introduction"),
                discord.SelectOption(label= "Getting Started", emoji= "🔰", value= "Getting Started"),
                discord.SelectOption(label= "League Invite", emoji= "🌐", value= "League Invite"),
                discord.SelectOption(label= "Game", emoji= "🕹️", value= "Game"),
                discord.SelectOption(label= "Rulebook", emoji= "📜", value= "Rulebook"),
                discord.SelectOption(label= "Roles", emoji= "📒", value= "Roles"),
                discord.SelectOption(label= "Apply", emoji= "💎", value= "Applications"),
            ], custom_id= "Information", placeholder= "Select module you'd like to read.")
            async def callback():
                pass
        
        await inter.guild.get_channel(914661528593125387).send(embed= embed, view= informationView())

        account_embed = discord.Embed(title= "HTL Accounts", description= "Click the button below to create an HTL Account!\n\nHTL Accounts...\n- Allow you to be signed to teams\n- Tracks your HTL career\n- And more!\n\n**You need to have verified through DoubleCounter before you can create an HTL Account.**")
        htl_account = ui.View()
        
        htl_account.add_item(ui.Button(label= "Create an Account", style= discord.ButtonStyle.blurple, custom_id= "start htl"))
                
            
        await inter.guild.get_channel(914661528593125387).send(embed= account_embed, view= htl_account)
        await inter.response.send_message(content="*The information embed has been sent.*")
        


    @app_commands.command()
    @app_commands.checks.has_any_role("Founder", "President", "Director")
    @app_commands.autocomplete(winning_team= teams_autocomplete, losing_team= teams_autocomplete)
    async def finalize_game(self, inter: discord.Interaction, winning_team: str, losing_team: str, game_id: str):
        winning_team = inter.guild.get_role(int(winning_team))
        losing_team = inter.guild.get_role(int(losing_team))

        game = get_game(game_id)
        player_ids = game["PlayerIds"]
        stats = game["Stats"]
        total_stats = {
            "Players": {},
            "Winning Team": 0,
            "Losing Team": 0
        }

        for category in stats.values():
            for id, subcategory in category.items():
                for name, value in subcategory.items():
                    if name == "Misses":
                        continue

                    try:
                        total_stats["Players"][int(id)] += value
                    except KeyError:
                        total_stats["Players"][int(id)] = value

        accounts = {"Winning Team": [], "Losing Team": []}
        active_accounts = {"Winning Team": [], "Losing Team": []}

        elo_lists = {
            "Winning Team": [],
            "Losing Team": []
        }

        for member in winning_team.members:
            account = databases["Player Data"]["Careers"].find_one({"DiscordId": member.id})

            if account:
                accounts["Winning Team"].append(account)
                if account["RobloxId"] in player_ids:
                    active_accounts["Winning Team"].append(account)
                    elo_lists["Winning Team"].append(account["Elo"])

                    total_stats["Winning Team"] += total_stats["Players"][account["RobloxId"]]

        for member in losing_team.members:
            account = databases["Player Data"]["Careers"].find_one({"DiscordId": member.id})

            if account:
                accounts["Losing Team"].append(account)
                if account["RobloxId"] in player_ids:
                    active_accounts["Losing Team"].append(account)
                    elo_lists["Losing Team"].append(account["Elo"])

                    total_stats["Losing Team"] += total_stats["Players"][account["RobloxId"]]

        affected = []
        updated_accounts = {
            "Winning Team": [],
            "Losing Team": []
        }

        team_elos = {
            "Winning Team": get_team_average(active_accounts["Winning Team"]),
            "Losing Team": get_team_average(active_accounts["Losing Team"])
        }

        for account in active_accounts["Winning Team"]:
            new_elo = round(new_rating(account["Elo"], team_elos["Losing Team"], True, total_stats["Players"][account["RobloxId"]], total_stats["Winning Team"]))
            affected.insert(0, {"Account": account, "OldElo": account["Elo"], "NewElo": new_elo, "Increase": True})

            new_account = account.copy()
            new_account["Elo"] = new_elo
            updated_accounts["Winning Team"].append(new_account)

            
        for account in active_accounts["Losing Team"]:
            new_elo = round(new_rating(account["Elo"], team_elos["Winning Team"], False, total_stats["Players"][account["RobloxId"]], total_stats["Losing Team"]))
            affected.append({"Account": account, "OldElo": account["Elo"], "NewElo": new_elo, "Increase": False})

            new_account = account.copy()
            new_account["Elo"] = new_elo
            updated_accounts["Losing Team"].append(new_account)

        strings = []

        for data in affected:
            roblox_username = await roclient.get_user(data["Account"]["RobloxId"])
            roblox_username = roblox_username.name
            discord_mention = bot.get_guild(htl_servers["League"]).get_member(data["Account"]["DiscordId"]).mention

            old_elo = data["OldElo"]
            new_elo = data["NewElo"]

            emoji = "<:elo_increase:1091348986813743336>"

            if not data["Increase"]:
                emoji = "<:elo_decrease:1091348984838242394>"

            strings.append(f"**{discord_mention}** ``{roblox_username}`` | *{old_elo}* {emoji} *{new_elo}*")
        
        elo_changes = discord.Embed(title= "Elo Changes", description= "The following Elos will be modified.")
        elo_changes.add_field(name= "``Players``", value= "> " + "\n> ".join(strings), inline= False)

        team_strings = []
        old_winning_team_elo = round(team_elos["Winning Team"])
        old_losing_team_elo = round(team_elos["Losing Team"])
        new_winning_team_elo = round(get_team_average(updated_accounts["Winning Team"]))
        new_losing_team_elo = round(get_team_average(updated_accounts["Losing Team"]))
        team_strings.append(f"**{winning_team.mention}** ``{winning_team.name}`` | *{old_winning_team_elo}* <:elo_increase:1091348986813743336> *{new_winning_team_elo}*")
        team_strings.append(f"**{losing_team.mention}** ``{losing_team.name}`` | *{old_losing_team_elo}* <:elo_decrease:1091348984838242394> *{new_losing_team_elo}*")
        
        elo_changes.add_field(name= "``Teams``", value= "> " + "\n> ".join(team_strings), inline= False)

        confirm = ui.View()
        
        class confirmButton(ui.Button):
            async def callback(self, interaction: discord.Interaction):
                if interaction.user.id != inter.user.id:
                    return

                for account in updated_accounts["Winning Team"]:
                    databases["Player Data"]["Careers"].update_one({"DiscordId": account["DiscordId"]}, {"$set": {"Elo": account["Elo"]}})

                for account in updated_accounts["Losing Team"]:
                    databases["Player Data"]["Careers"].update_one({"DiscordId": account["DiscordId"]}, {"$set": {"Elo": account["Elo"]}})

                elo_changes.description = ""

                await interaction.guild.get_channel(1093669850104221706).send(embed= elo_changes)
                await interaction.message.edit(embed= elo_changes, view= None)
                await interaction.response.send_message("***Changes confirmed!***", ephemeral= True)

                
        class cancelButton(ui.Button):
            async def callback(self, interaction: discord.Interaction):
                if interaction.user.id != inter.user.id:
                    return

                await interaction.message.delete()
                
        confirm.add_item(confirmButton(label= "Confirm", style= discord.ButtonStyle.green))
        confirm.add_item(cancelButton(label= "Cancel", style= discord.ButtonStyle.red))

        await inter.response.send_message(embed= elo_changes, view = confirm)
        await bot.tree.get_command("admin").get_command("leaderboard").get_command("update").callback(self= None, inter= inter)

    leaderboard = app_commands.Group(name= "leaderboard", description= "Change the HTL leaderboard")
    
    @leaderboard.command()
    @app_commands.checks.has_any_role("Founder", "President", "Director")
    async def create(self, inter: discord.Interaction):
        lb = discord.Embed(title= "HTL Leaderboard")

        teams = {}

        for role in inter.guild.roles:
            if isTeamRole(inter.guild.id, role.id):
                accounts = []

                for member in role.members:
                    profile = databases["Player Data"]["Careers"].find_one({"DiscordId": member.id})

                    if profile:
                        accounts.append(profile)
                try:
                    teams[role.id] = get_team_average(accounts)
                except Exception:
                    continue

        teams = sorted(teams.items(), reverse= True, key=lambda x:x[1])
        strings = []

        pos = 0
        for team in teams:
            pos += 1
            team_id = team[0]
            team_elo = team[1]
            team_elo = round(team_elo)

            team_role = inter.guild.get_role(team_id)

            string = f"**#{pos}** ``{team_elo}`` | **{team_role.name}** {team_role.mention}"
            strings.append(string)

        lb.add_field(name= "``Teams``", value= "> " + "\n> ".join(strings), inline= False)

        t = round(time.time())

        lb.add_field(name= "``Last Updated``", value= f"> <t:{t}>", inline= False)

        await inter.guild.get_channel(1024370000968044545).send(embed= lb)
        await inter.response.send_message(content= "Leaderboard has been created!", ephemeral= True)

    @leaderboard.command()
    @app_commands.checks.has_any_role("Founder", "President", "Director")
    async def update(self, inter: discord.Interaction, message: str= str(leaderboard_message_id)):
        msg = await inter.guild.get_channel(1024370000968044545).fetch_message(int(message))

        lb = discord.Embed(title= "HTL Leaderboard")

        teams = {}

        for role in inter.guild.roles:
            if isTeamRole(inter.guild.id, role.id):
                accounts = getTeamAccounts(role)

                try:
                    teams[role.id] = get_team_average(accounts)
                except Exception:
                    continue

        teams = sorted(teams.items(), reverse= True, key=lambda x:x[1])
        strings = []

        pos = 0
        for team in teams:
            pos += 1
            team_id = team[0]
            team_elo = team[1]
            team_elo = round(team_elo)

            team_role = inter.guild.get_role(team_id)

            string = f"**#{pos}** ``{team_elo}`` | **{team_role.name}** {team_role.mention}"
            strings.append(string)

        lb.add_field(name= "``Teams``", value= "> " + "\n> ".join(strings), inline= False)

        t = round(time.time())

        lb.add_field(name= "``Last Updated``", value= f"> <t:{t}>", inline= False)

        await msg.edit(embed= lb)



bot.tree.add_command(admin())