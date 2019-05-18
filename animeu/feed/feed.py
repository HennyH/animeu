# /animeu/feed/feed.py
#
# Route definitions for the authentication module.
#
# See /LICENCE.md for Copyright information
"""Route definitions for the authentication module."""
from flask import Blueprint, render_template, request

from .logic import (get_leaderboard_entries_data,
                    get_recent_battles_data,
                    LEADERBOARD_TO_DISPLAY_NAME)

# pylint: disable=invalid-name
feed_bp = Blueprint("feed_bp", __name__, template_folder="templates")

@feed_bp.route("/feed")
def feed(limit=20):
    """Display a feed of recent waifu battles."""
    leaderboard = request.args.get("leaderboard", "highELO")
    # pylint: disable=line-too-long
    leaderboard_entries = \
        list(get_leaderboard_entries_data(leaderboard=leaderboard, limit=limit))
    battles = get_recent_battles_data(limit=limit)
    return render_template(
        "feed.html",
        battles=battles,
        leaderboard_entries=leaderboard_entries,
        leaderboard_name=(
            LEADERBOARD_TO_DISPLAY_NAME.get(leaderboard, "Leaderboard")))
