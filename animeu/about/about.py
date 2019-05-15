# /animeu/about/about.py
#
# Route definitions for the about module.
#
# See /LICENCE.md for Copyright information
"""Route definitions for the about module."""
from http import HTTPStatus
from flask import Blueprint, render_template, Response
from flask_login import current_user, login_required

from animeu.data_loader import get_character_by_name

# pylint: disable=invalid-name
about_bp = Blueprint("about_bp", __name__, template_folder="templates")

@about_bp.route("/about_us")
def aboutus():
    return render_template("about_us.html")