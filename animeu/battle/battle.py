# /animeu/battle/battle.py
#
# Routes relating to the battle module.
#
# See /LICENCE.md for Copyright information
"""Routes relating to the battle module."""
import random

from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

from animeu.app import DATA_JSON

# pylint: disable=invalid-name
battle_bp = Blueprint("battle_bp",
                      __name__,
                      url_prefix="/battle",
                      template_folder="templates")

@battle_bp.route("/")
def battle():
    """Render a simple A vs. B battle screen."""
    try:
        character1 = random.choice(DATA_JSON)
        character1["pictures"]["gallery"] = \
            [p for p in character1["pictures"]["gallery"] if "23x32" not in p]
        character2 = random.choice(DATA_JSON)
        character2["pictures"]["gallery"] = \
            [p for p in character2["pictures"]["gallery"] if "23x32" not in p]
        return render_template('battle.html',
                               left=character1,
                               right=character2)
    except TemplateNotFound:
        abort(404)
