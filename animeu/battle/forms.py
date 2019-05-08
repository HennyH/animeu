# /animeu/battle/forms.py
#
# Forms for the battle module.
#
# See /LICENCE.md for Copyright information
"""Forms for the battle module."""
from flask_wtf import FlaskForm
from wtforms import  HiddenField, validators

class WaifuPickBattleForm(FlaskForm):
    """Form for the waifu pick battle."""

    winner_name = HiddenField(validators=[validators.DataRequired()])
    loser_name = HiddenField(validators=[validators.DataRequired()])
