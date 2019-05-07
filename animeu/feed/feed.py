# /animeu/feed/feed.py
#
# Route definitions for the authentication module.
#
# See /LICENCE.md for Copyright information
"""Route definitions for the authentication module."""
from flask import Blueprint, render_template

from animeu.models import WaifuPickBattle
from animeu.data_loader import get_character_by_name
from animeu.battle.battle import temp_fix_picutres

# pylint: disable=invalid-name
feed_bp = Blueprint("feed_bp", __name__, template_folder="templates")

@feed_bp.route("/feed")
def feed(limit=20):
    """Display a feed of recent waifu battles."""
    recent_battles = WaifuPickBattle.query\
        .order_by(WaifuPickBattle.date.desc())\
        .limit(limit)\
        .all()
    battle_summaries = [
        {
            "date": b.date,
            "winner": temp_fix_picutres(get_character_by_name(b.winner_name)),
            "loser": temp_fix_picutres(get_character_by_name(b.loser_name))
        }
        for b in recent_battles
    ]
    return render_template("feed.html", battles=battle_summaries)
