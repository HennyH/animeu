# /animeu/about/about.py
#
# Route definitions for the about module.
#
# See /LICENCE.md for Copyright information
"""Route definitions for the about module."""
from flask import Blueprint, render_template

# pylint: disable=invalid-name
about_bp = Blueprint("about_bp", __name__, template_folder="templates")

@about_bp.route("/about")
def about():
    """Render the about page."""
    return render_template("about.html")
