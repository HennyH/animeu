# /animeu/elo/__init__.py
#
# Entry point to the ELO module.
#
# See /LICENCE.md for Copyright information
"""Entry point to the ELO module."""
from collections import defaultdict

DEFAULT_RANK = 1000
K_FACTOR = 30

def calculate_expected_score(rank_a, rank_b):
    """Calculate the probability that the player will win or draw.

    Formula taken from:
    https://en.wikipedia.org/wiki/Elo_rating_system#Mathematical_details
    """
    return 1.0 / (1.0 + pow(10, (rank_b - rank_a) / 400.0))

def calculate_updated_ranking(rank_a, expected_score, actual_score, k_factor):
    """Update a ranking with the results of a game.

    Formula taken from:
    https://en.wikipedia.org/wiki/Elo_rating_system#Mathematical_details
    """
    return rank_a + k_factor * (actual_score - expected_score)

def calculate_elo_rankings(ordered_games, game_to_winner, game_to_loser):
    """Calculate the ELO rankings of players from an ordered set of games."""
    player_to_rank = defaultdict(lambda: DEFAULT_RANK)
    for game in ordered_games:
        winner = game_to_winner(game)
        loser = game_to_loser(game)
        # get the rankings of the players before the game started
        winner_rank = player_to_rank[winner]
        loser_rank = player_to_rank[loser]
        # calculate the expected scores for each player
        winner_expected_score = \
            calculate_expected_score(winner_rank, loser_rank)
        loser_expected_score = \
            calculate_expected_score(loser_rank, winner_rank)
        # determine new rankings for players based on the outcome of the game
        updated_winner_rank = calculate_updated_ranking(
            rank_a=winner_rank,
            expected_score=winner_expected_score,
            actual_score=1,
            k_factor=K_FACTOR
        )
        updated_loser_rank = calculate_updated_ranking(
            rank_a=loser_rank,
            expected_score=loser_expected_score,
            actual_score=0,
            k_factor=K_FACTOR
        )
        # update the rankings
        player_to_rank[winner] = updated_winner_rank
        player_to_rank[loser] = updated_loser_rank
    return player_to_rank
