# /animeu/feed/logic.py
#
# Controller functions for the feed module.
#
# See /LICENCE.md for Copyright information
"""Controller functions for the feed module."""
import json
from operator import itemgetter
from functools import partial

from animeu.common.func_helpers import compose
from animeu.data_loader import get_character_by_name
from animeu.models import ELORankingCalculation
from .queries import (query_most_battled_waifus,
                      query_most_winning_waifus,
                      query_most_recent_battles)

def get_elo_rankings(limit=20, reverse=True, **kwargs):
    """Get the current elo rankings for the top/bottom N players."""
    del kwargs
    latest_elo_calculation = ELORankingCalculation.query\
        .order_by(ELORankingCalculation.date.desc())\
        .first()
    if not latest_elo_calculation:
        return []
    name_elo_pairs = json.loads(latest_elo_calculation.rankings).items()
    ordered_name_elo_pairs = sorted(name_elo_pairs,
                                    key=itemgetter(1),
                                    reverse=reverse)
    entries = []
    for name, elo in ordered_name_elo_pairs[:limit]:
        character = get_character_by_name(name)
        entries.append({
            "en_name": character["names"]["en"][0],
            "jp_name": character["names"]["jp"][0],
            "gallery": character["pictures"]["gallery"],
            "counters": [
                {"title": "ELO", "count": int(elo), "class": "green-counter"}
            ]
        })
    return entries

def map_name_win_loss_result_to_leaderboard_entries(result):
    """Map a name/win/loss result to a leaderboard entry object."""
    character = get_character_by_name(result.name)
    return {
        "en_name": character["names"]["en"][0],
        "jp_name": character["names"]["jp"][0],
        "gallery": character["pictures"]["gallery"],
        "counters": [
            # pylint: disable=line-too-long
            {"title": "W", "count": int(result.wins), "class": "green-counter"},
            # pylint: disable=line-too-long
            {"title": "L", "count": int(result.losses), "class": "red-counter"},
        ]
    }

LEADERBOARD_TO_QUERY_FACTORY = {
    "winners": lambda *args, **kwargs: (
        map(map_name_win_loss_result_to_leaderboard_entries,
            query_most_winning_waifus(*args, **kwargs))
    ),
    "active": lambda *args, **kwargs: (
        map(map_name_win_loss_result_to_leaderboard_entries,
            query_most_battled_waifus(*args, **kwargs))
    ),
    "highELO": get_elo_rankings,
    "lowELO": partial(get_elo_rankings, reverse=False)
}
LEADERBOARD_TO_DISPLAY_NAME = {
    "winners": "Top Waifus",
    "active": "Active Waifus",
    "highELO": "Highest ELO",
    "lowELO": "Lowest ELO"
}

def get_leaderboard_entries_data(leaderboard=None, from_date=None, limit=20):
    """Get the data for a leaderboard type."""
    leaderboard = leaderboard or "winners"
    if leaderboard not in LEADERBOARD_TO_QUERY_FACTORY:
        raise ValueError(f"Unkown leaderboard type {leaderboard}.")
    return LEADERBOARD_TO_QUERY_FACTORY[leaderboard](from_date=from_date,
                                                     limit=limit)

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
