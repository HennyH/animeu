# /animeu/app.py
#
# Entrypoint which configures the animeu flask app.
#
# See /LICENCE.md for Copyright information
"""Entrypoint which configures the animeu flask app."""
import sys
import os
import json
import itertools
from functools import partial

try:
    import coverage
    coverage.process_startup()
except ImportError:
    print("Unable to import and start up coverage", file=sys.stderr)
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth


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
app.config["SQLALCHEMY_ECHO"] = \
    True if os.environ.get("SQLALCHEMY_ECHO") else False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = \
    os.environ.get("DATABASE",
                   os.environ.get("DATABASE_URL", "sqlite:///../app.db"))
if app.debug:
    print(f"USING DATABASE = {app.config['SQLALCHEMY_DATABASE_URI']}",
          file=sys.stderr)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# configre session management
login_manager = LoginManager(app)
login_manager.login_view = "auth_bp.login"
basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()

# pylint: disable=wrong-import-position,unused-import,wildcard-import,unused-wildcard-import
from animeu.models import *

# pylint: disable=wrong-import-position
from animeu.battle import battle_bp
# pylint: disable=wrong-import-position
from animeu.auth import auth_bp
# pylint: disable=wrong-import-position
from animeu.feed import feed_bp
# pylint: disable=wrong-import-position
from animeu.api import api_bp
# pylint: disable=wrong-import-position
from animeu.profile import profile_bp
# pylint: disable=wrong-import-position
from animeu.admin import admin_bp
# pylint: disable=wrong-import-position
from animeu.about import about_bp
# pylint: disable=wrong-import-position
from animeu.info import info_bp

app.register_blueprint(battle_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(feed_bp)
app.register_blueprint(api_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(about_bp)
app.register_blueprint(info_bp)

@app.context_processor
def jinja_utilities():
    """Utilities to expose in jinja2 templates."""
    return {"debug": partial(print, file=sys.stderr), "json": json.dumps}

@app.template_filter('chain')
def chain_filter(iterable):
    """Expose the chain.from_iterable function in templates."""
    return itertools.chain.from_iterable(iterable)

@app.route("/")
def index():
    """Root of the site."""
    return redirect(url_for("battle_bp.battle"))
