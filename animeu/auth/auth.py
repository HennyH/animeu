# /animeu/auth/routes.py
#
# Route definitions for the authentication module.
#
# See /LICENCE.md for Copyright information
"""Route definitions for the authentication module."""
from flask import Blueprint, render_template, request, url_for, redirect
from flask_login import login_user, logout_user, current_user
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import BooleanField, StringField, PasswordField, validators
from wtforms.fields.html5 import EmailField
from werkzeug.security import generate_password_hash, check_password_hash

from animeu.models import User
from animeu.app import db
from animeu.common.request_helpers import arg_redirect
from .forms import LoginForm, RegisterForm
from .logic import hash_password, check_password, maybe_find_user

# pylint: disable=invalid-name
auth_bp = Blueprint("auth_bp", __name__, template_folder="templates")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Render the login page."""
    form = LoginForm()
    if form.validate_on_submit():
        maybe_user = maybe_find_user(request.form["email"],
                                     request.form["password"])
        if maybe_user:
            login_user(maybe_user)
            return arg_redirect(request, "next")
        form.email.errors.append("Unrecognised email or password.")
    return render_template("login.html", form=form)

@auth_bp.route("/logout")
def logout():
    """Log the current user out if they are authenticated."""
    if current_user.is_authenticated:
        logout_user()
    return arg_redirect(request, "next", fallback_endpoint="auth_bp.login")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Render the register page and respond to form submission."""
    form = RegisterForm()
    if request.method == "POST":
        # make sure the email isn't already taken.
        if maybe_find_user(form.email.data, password=None):
            form.validate()
            form.email.errors.append("Email is already registered.")
        elif form.validate_on_submit():
            new_user = User(email=form.email.data,
                            username=form.username.data,
                            password_hash=hash_password(form.password.data))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return arg_redirect(request, "next")
    return render_template("register.html", form=form, register=True)
