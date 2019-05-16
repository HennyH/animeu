# /animeu/info/info.py
#
# Route definitions for the info module.
#
# See /LICENCE.md for Copyright information
"""Route definitions for the info module."""
from http import HTTPStatus
from flask import Blueprint, render_template, url_for, Response
from flask_login import current_user, login_required

from animeu.app import db
from animeu.profile.queries import query_has_favourited_waifus
from animeu.data_loader import get_character_by_name
from animeu.profile.logic import (maybe_get_favourited_waifu,
                    favourite_a_waifu,
                    unfavourite_a_waifu)

# pylint: disable=invalid-name
info_bp = Blueprint("info_bp", __name__, template_folder="templates")

@info_bp.route("/info/<char_name>")
def info(char_name):
    character = get_character_by_name(char_name)
    name_to_favourited = \
        query_has_favourited_waifus(current_user.id, char_name[0])
    character["favourited"] = name_to_favourited[char_name[0]]
    return render_template("info.html", character=character)

@info_bp.route("/favourite/<name>", methods=["POST"])
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