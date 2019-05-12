# /animeu/feed/logic.py
#
# Controller functions for the feed module.
#
# See /LICENCE.md for Copyright information
"""Controller functions for the feed module."""
from animeu.data_loader import get_character_by_name
from .queries import (query_most_battled_waifus,
                      query_most_winning_waifus,
                      query_most_recent_battles)

LEADERBOARD_TO_QUERY_FACTORY = {
    "winners": query_most_winning_waifus,
    "active": query_most_battled_waifus
}
LEADERBOARD_TO_DISPLAY_NAME = {
    "winners": "Top Waifus",
    "active": "Active Waifus"
}

def get_leaderboard_entries_data(leaderboard=None, from_date=None, limit=20):
    """Get the data for a leaderboard type."""
    leaderboard = leaderboard or "winners"
    if leaderboard not in LEADERBOARD_TO_QUERY_FACTORY:
        raise ValueError(f"Unkown leaderboard type {leaderboard}.")
    results = LEADERBOARD_TO_QUERY_FACTORY[leaderboard](from_date=from_date,
                                                        limit=limit)
    entries = []
    for result in results:
        character = get_character_by_name(result.name)
        entries.append({
            "en_name": character["names"]["en"][0],
            "jp_name": character["names"]["jp"][0],
            "win_count": result.wins,
            "loss_count": result.losses,
            "gallery": character["pictures"]["gallery"]
        })
    return entries

def get_recent_battles_data(limit=20):
    """Get the data for the most recent battles."""
    return [
        {
            "date": b.date,
            "winner": get_character_by_name(b.winner_name),
            "loser": get_character_by_name(b.loser_name)
        }
        for b in query_most_recent_battles(limit)
    ]
