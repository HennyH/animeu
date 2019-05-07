# /animeu/feed/feed.py
#
# Route definitions for the authentication module.
#
# See /LICENCE.md for Copyright information
"""Route definitions for the authentication module."""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify

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
    return render_template("feed.html", battles=battle_summaries)

@feed_bp.route("/top-waifus")
def top_waifus():
    """Return the most winning waifus."""
    return jsonify(query_most_winning_waifus())

@feed_bp.route("/active-waifus")
def active_waifus():
    """Return the most active waifus battle wise."""
    from_date = datetime.now() + timedelta(days=-30)
    return jsonify(query_most_battled_waifus(from_date))
