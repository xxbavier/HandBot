import math

starting_elo = 1200

def get_estimated_score(target_rating: float, opponent_rating: float):
    estimated_scores = 1/(1 + math.pow(10, (opponent_rating - target_rating)/400))

    return estimated_scores

def get_team_average(accounts: list):
    elos = [account["Elo"] for account in accounts]

    return sum(elos)/len(elos)

def get_total_elo(accounts):
    elo = 0

    for account in accounts:
        elo += account["Elo"]

    return elo

def new_rating(target_rating: float, opponent_rating: float, target_won: bool, player_stats: int, total_stats: int):
    won_binary = 0
    increment = 120

    if target_won:
        multipler = player_stats/total_stats
    else:
        multipler = (total_stats - player_stats)/total_stats

    if target_won:
        won_binary = 1

    rating = target_rating + increment * (won_binary - get_estimated_score(target_rating, opponent_rating)) * multipler

    return rating

'''def get_estimated_score(target_rating: float, opponent_ratings: list):
    op_ratings = 0

    for opponent in opponent_ratings:
        op_ratings += 1/(1 + math.pow(10, (opponent - target_rating)/400))

    op_ratings /= (len(opponent_ratings) * max(len(opponent_ratings) - 1, 1))/2

    return op_ratings

def get_stats_score(account, game_stats: dict):
    stats_score = 0

    for stats_category in game_stats.values():
        stats_category = stats_category[str(account["RobloxId"])]

        for name, stats_subcategory in stats_category.items():
            print(name, stats_subcategory)
            if name == "Misses":
                continue

            stats_score += stats_subcategory

    return stats_score

def get_player_place(account: list, team: dict[int: dict], game_stats: dict):
    score = get_stats_score(account, game_stats)
    pos = 1

    for member in team:
        if score < get_stats_score(member, game_stats):
            pos += 1

    return pos

def score(place, team):
    return (len(team) - place)/((len(team) * max(len(team) - 1, 1))/2)

def new_rating(target_account: float, opponent_ratings: list, team: dict[int: dict], target_won: bool, game_stats):
    rating = target_account["Elo"] + 120 * (len(opponent_ratings) - 1) * (score(get_player_place(target_account, team, game_stats), team)) - get_estimated_score(target_account["Elo"], opponent_ratings)

    return rating'''