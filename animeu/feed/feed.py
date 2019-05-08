# /animeu/feed/feed.py
#
# Route definitions for the authentication module.
#
# See /LICENCE.md for Copyright information
"""Route definitions for the authentication module."""
from flask import Blueprint, render_template

from animeu.data_loader import get_character_by_name
from .queries import (query_most_battled_waifus,
                      query_most_winning_waifus,
                      query_most_recent_battles)

# pylint: disable=invalid-name
feed_bp = Blueprint("feed_bp", __name__, template_folder="templates")

@feed_bp.route("/feed")
def feed(limit=20):
    """Display a feed of recent waifu battles."""
    recent_battles = query_most_recent_battles(limit)
    battle_summaries = [
        {
            "date": b.date,
            "winner": get_character_by_name(b.winner_name),
            "loser": get_character_by_name(b.loser_name)
        }
        for b in recent_battles
    ]
    top_waifus = []
    for result in query_most_winning_waifus():
        character = get_character_by_name(result.name)
        top_waifus.append({
            "en_name": character["names"]["en"][0],
            "jp_name": character["names"]["jp"][0],
            "win_count": result.wins,
            "loss_count": result.losses,
            "gallery": character["pictures"]["gallery"]
        })
    active_waifus = []
    for result in query_most_battled_waifus():
        character = get_character_by_name(result.name)
        active_waifus.append({
            "en_name": character["names"]["en"][0],
            "jp_name": character["names"]["jp"][0],
            "win_count": result.wins,
            "loss_count": result.losses,
            "gallery": character["pictures"]["gallery"]
        })
    return render_template("feed.html",
                           battles=battle_summaries,
                           top_waifus=top_waifus,
                           active_waifus=active_waifus)
