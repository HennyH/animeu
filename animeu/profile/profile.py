# /animeu/profile/profile.py
#
# Route definitions for the profile module.
#
# See /LICENCE.md for Copyright information
"""Route definitions for the profile module."""
from http import HTTPStatus
from flask import Blueprint, render_template, Response
from flask_login import current_user, login_required

from animeu.data_loader import get_character_by_name
from .queries import (get_favourite_waifu_list,
                      get_favourited_waifu_battles)
from .logic import (maybe_get_favourited_waifu,
                    favourite_a_waifu,
                    unfavourite_a_waifu)

# pylint: disable=invalid-name
profile_bp = Blueprint("profile_bp", __name__, template_folder="templates")

@profile_bp.route("/profile")
@login_required
def profile():
    """Return the users profile page."""
    best_waifus = []
    for result in get_favourite_waifu_list(current_user.id):
        character = get_character_by_name(result.character_name)
        best_waifus.append({
            "en_name": character["names"]["en"][0],
            "jp_name": character["names"]["jp"][0],
            "date-favour": result.date.strftime("%d %b %Y"),
            "gallery": character["pictures"]["gallery"]
        })
    recent_battles = get_favourited_waifu_battles(current_user.id)
    battle_summaries = [
        {
            "date": b.date,
            "winner": get_character_by_name(b.winner_name),
            "loser": get_character_by_name(b.loser_name)
        }
        for b in recent_battles
    ]
    return render_template("profile.html",
                           best_waifus=best_waifus,
                           battles=battle_summaries)

@profile_bp.route("/favourite/<name>", methods=["POST"])
@login_required
def favourite(name):
    """Favourite a character."""
    maybe_favourted_waifu = maybe_get_favourited_waifu(
        user_id=current_user.id,
        character_name=name
    )
    if maybe_favourted_waifu:
        unfavourite_a_waifu(user_id=current_user.id, character_name=name)
        return Response(status=HTTPStatus.NO_CONTENT)
    waifu = favourite_a_waifu(user_id=current_user.id, character_name=name)
    return Response(str(waifu.id), status=HTTPStatus.CREATED)
