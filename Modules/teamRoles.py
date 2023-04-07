import discord
from settings import bot
from Modules.database import databases

coachRoles = {
    'TO': 917068655928442930, # TO
    'GM': 917068674626646027, # GM
}

def teamCheck(user, htl):
    '''
    Checks to see if a player is on a valid team.
    
    Returns [True, team_role] if player is on a team.
    Returns [False, team_role] if player is not on a team.
    '''

    membership = htl.get_role(917043822402338886)
    end = htl.get_role(917043508509032508)

    onTeam = False
    teamRole = None

    for x in user.roles:
        if x.position < end.position and x.position > membership.position:
            onTeam = True
            teamRole = x
            break
        
    return [onTeam, teamRole]

def getTeamAccounts(team: discord.Role):
    accounts = []

    for member in team.members:
        profile = databases["Player Data"]["Careers"].find_one({"DiscordId": member.id})

        if profile:
            accounts.append(profile)

    return accounts

def isTeamRole(guild_id: str, role_id: int):
    role = bot.get_guild(guild_id).get_role(role_id)

    if role.position < bot.get_guild(guild_id).get_role(917043508509032508).position and role.position > bot.get_guild(guild_id).get_role(917043822402338886).position:
       return True
    else:
        return False

def coachCheck(user, htl):
    '''
    Returns coaching level of a member.
    Returns 3 if user is a Team Owner.
    Returns 2 if user is an Head Coach.
    Returns 1 if user is an Assistant Coach.
    Returns 0 if user is not a coach.
    '''

    if htl.get_role(coachRoles["TO"]) in user.roles:
        return 3
    
    elif htl.get_role(coachRoles["GM"]) in user.roles:
        return 2

    #elif htl.get_role(assistantCoach) in user.roles:
    #    return 1
    
    return 0

def teamCheckBool(inter: discord.interactions.Interaction):
    '''
    Checks to see if a player is on a valid team.
    
    Returns [True, team_role] if player is on a team.
    Returns [False, team_role] if player is not on a team.
    '''

    membership = inter.guild.get_role(917043822402338886)
    end = inter.guild.get_role(917043508509032508)

    onTeam = False

    for x in inter.user.roles:
        if x.position < end.position and x.position > membership.position:
            onTeam = True
            break
        
    return onTeam
