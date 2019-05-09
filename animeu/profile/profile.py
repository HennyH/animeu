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
from animeu.feed.queries import query_most_winning_waifus
from .logic import (maybe_get_favourited_waifu,
                    favourite_a_waifu,
                    unfavourite_a_waifu)

# pylint: disable=invalid-name
profile_bp = Blueprint("profile_bp", __name__, template_folder="templates")

@profile_bp.route("/profile")
@login_required
def profile():
    """Return the users profile page."""
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
    return render_template("profile.html",
                           top_waifus=top_waifus)

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
