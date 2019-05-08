# /animeu/profile/profile.py
#
# Route definitions for the profile module.
#
# See /LICENCE.md for Copyright information
"""Route definitions for the profile module."""
from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from animeu.data_loader import get_character_by_name
from .queries import (query_most_winning_waifus)

# pylint: disable=invalid-name
profile_bp = Blueprint("profile_bp", __name__, template_folder="templates")

@profile_bp.route("/profile")
@login_required
def profile():
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
