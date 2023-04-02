import math

starting_elo = 1200

def get_estimated_score(target_rating: float, opponent_rating: float):
    estimated_scores = 1/(1 + math.pow(10, (opponent_rating - target_rating)/400))

    return estimated_scores

def new_rating(target_rating: float, opponent_rating: float, target_won: bool):
    won_binary = 0

    if target_won:
        won_binary = 1

    rating = target_rating + 120 * (won_binary - get_estimated_score(target_rating, opponent_rating))

    return rating