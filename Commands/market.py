import discord
from discord import app_commands, ui
from Modules.teamRoles import teamCheck, coachRoles, coachCheck, teamCheckBool, getTeamAccounts
from Modules.elo_system import get_total_elo, get_team_average
from Modules.database import databases
from Modules.member_strings import *
from settings import transactions_enabled, transactions_channel_id, bot, htl_servers, team_cap
import time

def transactionEmbed(emoji, team_role):
    embed= discord.Embed(title= "{} {}".format(emoji, team_role.name), description= "", colour= team_role.color)

    return embed

@app_commands.guild_only()
class market(app_commands.Group, name= "market", description= "Where coaches can manage their team."):
    def isCoach(member) -> list[bool, discord.Role]:
        pass

    trades = app_commands.Group(name= "trades", description= "Manage your trades.")
    
    @trades.command()
    @app_commands.checks.has_any_role("Team Owner", "General Manager")
    async def create(self, inter: discord.interactions.Interaction) -> None:
        embed = discord.Embed()

    contracts = app_commands.Group(name= "contracts", description="Manage contracts.")

    @contracts.command()
    @app_commands.checks.has_any_role("Team Owner", "General Manager")
    async def offer(self, inter: discord.interactions.Interaction, member: discord.User) -> None:
        pass

    @contracts.command()
    @app_commands.checks.has_any_role("Team Owner", "General Manager")
    async def view(self, inter: discord.interactions.Interaction) -> None:
        pass

    def canPromotePlayer(self, inter: discord.interactions.Interaction):
        valid = True

        info = teamCheck(inter.user, inter.guild)
        onTeam = info[0]
        teamRole = info[1]

        if onTeam:
            coachCount = 0

            for member in teamRole.members:
                if inter.guild.get_role(coachRoles["GM"]) in member.roles:
                    coachCount += 1

            if coachCount >= 2:
                valid = False
        
        return valid

    @app_commands.command(description="Promote a player to General Manager.")
    @app_commands.checks.has_any_role("Team Owner")
    async def promote(self, inter: discord.interactions.Interaction, member: discord.Member):
        author = inter.user
        htl = inter.guild

        team_info = teamCheck(author, htl)

        valid_team = team_info[0]
        team_role = team_info[1]

        if not valid_team:
            raise Exception("You must be a team owner on a valid team to use this command.")

        if not transactions_enabled:
            raise Exception("Transactions are closed.")

        if author == member:
            raise Exception("Attempt to use command on self.")

        if teamCheck(member, htl)[1] != team_role:
            raise Exception("Player must be on the same team as you.")

        if coachCheck(member, htl) >= 2:
            raise Exception("Player is either already at the requested coaching level or is above it. Use /demote to demote players.")
            
        if not self.canPromotePlayer(inter):
            raise Exception("You already have 2 General Managers.")
        
        for e in htl.emojis:
            if team_role.name.find(e.name) > -1:
                break
        
        embed = transactionEmbed(e, team_role)

        noti= discord.Embed(title= "You are now a General Manager for: {} {}".format(e, team_role.name), description= "", colour= team_role.color)
        noti.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)

        await member.send(
            embed= noti
        )

        await member.add_roles(htl.get_role(coachRoles["GM"]))

        embed.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)
        embed.add_field(name="``Promotion``", value= "{} ({})".format(member.mention, member.name), inline=False)

        await htl.get_channel(transactions_channel_id).send(
            embed= embed
        )
        
        await author.send(
            content = "***You have just made a transaction.***",
            embed= embed
        )

        await inter.response.send_message(
            content= "***Check your Direct Messages with {} ({}).***".format(bot.user.mention, bot.user.name),
            ephemeral= True
        )

    @app_commands.command(description="Demote a General Manager to player.")
    @app_commands.checks.has_any_role("Team Owner")
    async def demote(self, inter: discord.interactions.Interaction, member: discord.Member):
        author = inter.user
        htl = inter.guild

        team_info = teamCheck(author, htl)

        valid_team = team_info[0]
        team_role = team_info[1]

        if not valid_team:
            raise Exception("You must be a team owner on a valid team to use this command.")

        if not transactions_enabled:
            raise Exception("Transactions are closed.")

        if author == member:
            raise Exception("Attempt to use command on self.")

        if teamCheck(member, htl)[1] != team_role:
            raise Exception("Player must be on the same team as you.")

        if coachCheck(member, htl) != 2:
            raise Exception("Player is not a General Manager.")
        
        for e in htl.emojis:
            if team_role.name.find(e.name) > -1:
                break
        
        embed = transactionEmbed(e, team_role)

        noti= discord.Embed(title= "You are no longer a General Manager for: {} {}".format(e, team_role.name), description= "", colour= team_role.color)
        noti.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)

        await member.send(
            embed= noti
        )

        await member.remove_roles(htl.get_role(coachRoles["GM"]))

        embed.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)
        embed.add_field(name="``Demotion``", value= "{} ({})".format(member.mention, member.name), inline=False)

        await htl.get_channel(transactions_channel_id).send(
            embed= embed
        )
        
        await author.send(
            content = "***You have just made a transaction.***",
            embed= embed
        )

        await inter.response.send_message(
            content= "***Check your Direct Messages with {} ({}).***".format(bot.user.mention, bot.user.name),
            ephemeral= True
        )

    @app_commands.command(description="Demand a release from your team.")
    @app_commands.check(teamCheckBool)
    async def demand(self, inter: discord.interactions.Interaction, reason: str):
        if not transactions_enabled:
            raise Exception("Transactions are closed.")

        author = inter.user
        htl = bot.get_guild(htl_servers["League"])

        team_info = teamCheck(author, htl)
        coach_info = coachCheck(author, htl)

        tick = int(time.time())
        last_tick = None
        
        try:
            cursor = databases['Player Data']["Demands"].find_one({'_id': author.id})

            last_tick = cursor["PreviousDemand"]
        except:
            pass

        if coach_info == 3 or not team_info[0]:
            raise Exception("You must be on a valid team and not be a Team Owner to use this command.")

        if last_tick:
            if tick - last_tick <= 604800:
                raise Exception("You are on cooldown! You can demand again in around {} days.".format(round((604800 - (tick - last_tick))/86400, 2)))

        try:
            databases["Player Data"]["Demands"].insert_one({'_id': author.id, "PreviousDemand": tick})
        except:
            databases["Player Data"]["Demands"].update_one({'_id': author.id}, {'$set': {"PreviousDemand": tick}})

        await author.remove_roles(
            team_info[1],
            htl.get_role(917068674626646027) # HC
        )

        for e in htl.emojis:
            if team_info[1].name.find(e.name) > -1:
                break
        
        embed = transactionEmbed(e, team_info[1])
        embed.add_field(name= "``Demanded a Release``", value= "{} ({})".format(author.mention, author.name), inline=False)

        if reason:
            embed.add_field(name= "``Reason``", value= reason, inline=False)

        await htl.get_channel(917102767208816680).send(
            embed= embed
        )

        await bot.tree.get_command("admin").get_command("leaderboard").get_command("update").callback(self= None, inter= inter)

    @app_commands.command(description="Remove players from your team's roster.")
    @app_commands.checks.has_any_role("Team Owner", "General Manager")
    async def release(self, inter: discord.interactions.Interaction, player: discord.Member):
        profile = databases["Player Data"]["Careers"].find_one({"DiscordId": inter.user.id})

        if not profile:
            raise Exception("You need an HTL Account to use this command.")

        if not transactions_enabled:
            raise Exception("Transactions are closed.")
            
        author = inter.user
        htl = bot.get_guild(htl_servers["League"])

        coach_level = coachCheck(author, htl)
        team_info = teamCheck(author, htl)

        valid_team = team_info[0]
        team_role = team_info[1]
        
        for e in htl.emojis:
            if team_role.name.find(e.name) > -1:
                break
        
        embed = transactionEmbed(e, team_role)

        if teamCheck(player, htl)[1] != team_role:
            raise Exception("Player must be on your team to use this command.")
        
        await player.remove_roles(team_role, htl.get_role(coachRoles["GM"]))

        noti= discord.Embed(title= "You have been released from: {} {}".format(e, team_role.name), description= "", colour= discord.Color.red())
        noti.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)

        await player.send(
            embed= noti
        )

        embed.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)
        embed.add_field(name="``Release``", value= f"{player.mention} ({player.name})", inline=False)

        team_accounts = getTeamAccounts(team_role)
        team_elo = get_total_elo(team_accounts)
        target_elo = team_elo + profile["Elo"]
        elo_cap = team_cap * 1200

        average = get_team_average(team_accounts)
        embed.add_field(name=f"``{team_role.name}``", value= f"> **Roster Size:** *{len(team_role.members)}*\n> **Elo Cap:** *{target_elo}/{elo_cap}*\n> **Elo Average:** *{round(average)}*", inline=False)

        await htl.get_channel(transactions_channel_id).send(
            embed= embed
        )
        
        await author.send(
            content = "***You have just made a transaction.***",
            embed= embed
        )

        await inter.response.send_message(
            content= "***Check your Direct Messages with {} ({}).***".format(bot.user.mention, bot.user.name),
            ephemeral= True
        )

        await bot.tree.get_command("admin").get_command("leaderboard").get_command("update").callback(self= None, inter= inter)
    
    @app_commands.command(description="Add players to your team's roster.")
    @app_commands.checks.has_any_role("Team Owner", "General Manager")
    async def sign(self, inter: discord.interactions.Interaction, player: discord.Member):
        profile = databases["Player Data"]["Careers"].find_one({"DiscordId": inter.user.id})

        if not profile:
            raise Exception("You need an HTL Account to use this command.")

        if not transactions_enabled:
            raise Exception("Transactions are closed")

        author = inter.user
        htl = bot.get_guild(htl_servers["League"])

        team_info = teamCheck(author, htl)

        valid_team = team_info[0]
        team_role = team_info[1]
        
        for e in htl.emojis:
            if team_role.name.find(e.name) > -1:
                break
        
        embed = transactionEmbed(e, team_role)

        profile = databases['Player Data']["Careers"].find_one({'DiscordId': player.id})
        team_elo = get_total_elo(getTeamAccounts(team_role))
        elo_cap = team_cap * 1200

        if profile:
            target_elo = team_elo + profile["Elo"]

        if not profile:
            missing_account = discord.Embed(title= "You do not have an HTL Account!", description= "A team coach has attempted to sign you; however, you do not have an HTL Account!\n\nClick the button to create an account.")

            class view(ui.View):
                @ui.button(label= "Create an Account", style= discord.ButtonStyle.blurple)
                async def callback(self, inter: discord.Interaction, b):
                    await bot.tree.get_command("account").get_command("create").callback(self= None, inter= inter)


            await player.send(embed= missing_account, view= view())
            raise Exception("Player does not have an HTL Account.")
        
        elif teamCheck(player, htl)[0]:
            raise Exception("Player is already on a team.")

        elif team_elo + profile["Elo"] > team_cap * 1200:
            raise Exception(f"You need ``{target_elo - elo_cap}`` more Elo space available to make this transaction")

        elif player.bot:
            raise Exception("You can not sign bots!")

        elif not (inter.guild.get_role(910371139803553812) in player.roles):
            role = inter.guild.get_role(910371139803553812)

            raise Exception(f"Player does not have the {role.mention} role.")    

        await player.add_roles(team_role)

        noti= discord.Embed(title= "You have been signed to: {} {}".format(e, team_role.name), description= "If you did not give permission to this user to sign you, please create a support ticket in <#917085749030031390>.", colour= team_role.color)
        noti.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)

        await player.send(
            embed= noti
        )

        embed.add_field(name="``Coach``", value= "{} ({})".format(author.mention, author.name), inline=False)
        embed.add_field(name="``Sign``", value= f"{player.mention} ({player.name})", inline=False)
        
        average = get_team_average(getTeamAccounts(team_role))
        embed.add_field(name=f"``{team_role.name}``", value= f"> **Roster Size:** *{len(team_role.members)}*\n> **Elo Cap:** *{target_elo}/{elo_cap}*\n> **Elo Average:** *{round(average)}*", inline=False)

        await htl.get_channel(transactions_channel_id).send(
            embed= embed
        )
        
        await author.send(
            content = "***You have just made a transaction.***",
            embed= embed
        )

        await inter.response.send_message(
            content= "***Check your Direct Messages with {} ({}).***".format(bot.user.mention, bot.user.name),
            ephemeral= True
        )

        await bot.tree.get_command("admin").get_command("leaderboard").get_command("update").callback(self= None, inter= inter)

bot.tree.add_command(market())