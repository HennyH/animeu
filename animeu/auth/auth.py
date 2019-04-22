# /animeu/auth/routes.py
#
# Route definitions for the authentication module.
#
# See /LICENCE.md for Copyright information
"""Route definitions for the authentication module."""
from flask import Blueprint, render_template

# pylint: disable=invalid-name
auth_bp = Blueprint("auth_bp",
                    __name__,
                    url_prefix="/auth",
                    template_folder="templates")

@auth_bp.route("/login")
def login():
    """Render the login page."""
    return render_template("login.html")
