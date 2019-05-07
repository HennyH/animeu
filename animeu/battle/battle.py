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
    character1 = random.choice(characters)
    character2 = random.choice(characters)
    return render_template(
        "battle.html",
        left=character1,
        left_form=WaifuPickBattleForm(
            winner_name=character1["names"]["en"][0],
            loser_name=character2["names"]["en"][0],
        ),
        right=character2,
        right_form=WaifuPickBattleForm(
            winner_name=character2["names"]["en"][0],
            loser_name=character1["names"]["en"][0],
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
