# /animeu/app.py
#
# Entrypoint which configures the animeu flask app.
#
# See /LICENCE.md for Copyright information
"""Entrypoint which configures the animeu flask app."""
import os
import sys
from functools import partial

from flask import Flask, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user

# pylint: disable=invalid-name
app = Flask(__name__)
app.config['SECRET_KEY'] = \
    os.environ.get("SECRET_KEY",
                   "a_secret_at_least_32_bytes_long_for_security")
app.config['WTF_CSRF_SECRET_KEY'] = \
    os.environ.get("WTF_CSRF_SECRET_KEY", "a_secret_csrf_key")
# both of these recaptcha keys are provided by the google recaptcha FAQ
# here for testing purposes: https://developers.google.com/recaptcha/docs/faq
app.config["RECAPTCHA_PUBLIC_KEY"] = \
    os.environ.get("RECAPTCHA_PUBLIC_KEY",
                   "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI")
app.config["RECAPTCHA_PRIVATE_KEY"] = \
    os.environ.get("RECAPTCHA_PRIVATE_KEY",
                   "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe")
app.config["RECAPTCHA_DATA_ATTRS"] = {"callback": "recaptchaOk"}
# see https://stackoverflow.com/a/33790196 for more information
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = \
    os.environ.get("DATABASE", "sqlite:///app.db")
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# configre session management
login_manager = LoginManager(app)
login_manager.login_view = "auth_bp.login"

# pylint: disable=wrong-import-position,unused-import,wildcard-import,unused-wildcard-import
from animeu.models import *

# pylint: disable=wrong-import-position
from animeu.battle import battle_bp
# pylint: disable=wrong-import-position
from animeu.auth import auth_bp

app.register_blueprint(battle_bp)
app.register_blueprint(auth_bp)

@app.context_processor
def jinja_utilities():
    return {"debug": partial(print, file=sys.stderr)}

@app.route("/")
def index():
    return redirect("/battle")
