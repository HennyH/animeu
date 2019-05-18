# /animeu/info/info.py
#
# Route definitions for the info module.
#
# See /LICENCE.md for Copyright information
"""Route definitions for the info module."""
from http import HTTPStatus
from flask import Blueprint, render_template
from flask_login import current_user, login_required

from animeu.api import error_response
from animeu.profile.queries import query_has_favourited_waifus
from animeu.data_loader import get_character_by_name
from .queries import query_character_win_loss_counts, query_character_elo

# pylint: disable=invalid-name
info_bp = Blueprint("info_bp", __name__, template_folder="templates")

@info_bp.route("/info/<character_name>")
@login_required
def info(character_name):
    """Return an info page for a character."""
    maybe_character = get_character_by_name(character_name)
    if maybe_character is None:
        return error_response(
            HTTPStatus.NOT_FOUND,
            f"Character with name '{character_name}' not found"
        )
    name_to_favourited = \
        query_has_favourited_waifus(current_user.id, [character_name])
    win_loss_counts = query_character_win_loss_counts(character_name)
    elo_rank = query_character_elo(character_name)
    counters = [
        # pylint: disable=line-too-long
        {"title": "ELO", "count": int(elo_rank) if elo_rank else None, "class": "green-counter"},
        # pylint: disable=line-too-long
        {"title": "W", "count": win_loss_counts.wins, "class": "green-counter"},
        # pylint: disable=line-too-long
        {"title": "L", "count": win_loss_counts.losses, "class": "red-counter"},
    ]
    maybe_character["favourited"] = name_to_favourited[character_name]
    return render_template("info.html",
                           character=maybe_character,
                           counters=counters)
