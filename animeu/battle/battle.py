# /animeu/battle/battle.py
#
# Routes relating to the battle module.
#
# See /LICENCE.md for Copyright information
"""Routes relating to the battle module."""
from datetime import datetime
import random

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from animeu.app import db
from animeu.data_loader import load_character_data
from animeu.models import WaifuPickBattle
from animeu.profile.queries import query_has_favourited_waifus
from .forms import WaifuPickBattleForm

# pylint: disable=invalid-name
battle_bp = Blueprint("battle_bp",
                      __name__,
                      url_prefix="/battle",
                      template_folder="templates")

@battle_bp.route("/", methods=["GET"])
@login_required
def battle():
    """Render a simple A vs. B battle screen."""
    characters = load_character_data()
    left_character = random.choice(characters)
    right_character = random.choice(characters)
    left_name = left_character["names"]["en"][0]
    right_name = right_character["names"]["en"][0]
    name_to_favourited = \
        query_has_favourited_waifus(current_user.id, [left_name, right_name])
    left_character["favourited"] = name_to_favourited[left_name]
    right_character["favourited"] = name_to_favourited[right_name]
    return render_template(
        "battle.html",
        left=left_character,
        left_form=WaifuPickBattleForm(
            winner_name=left_name,
            loser_name=right_character["names"]["en"][0],
        ),
        right=right_character,
        right_form=WaifuPickBattleForm(
            winner_name=right_name,
            loser_name=left_character["names"]["en"][0],
        )
    )

@battle_bp.route("/", methods=["POST"])
@login_required
def submit_battle():
    """Record a battle result."""
    form = WaifuPickBattleForm()
    if form.validate_on_submit():
        result = WaifuPickBattle(
            user_id=current_user.id,
            date=datetime.now(),
            winner_name=form.winner_name.data,
            loser_name=form.loser_name.data
        )
        db.session.add(result)
        db.session.commit()
    return redirect(url_for("battle_bp.battle"))
