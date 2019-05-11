# /animeu/models.py
#
# Database models for the animeu site.
#
# See /LICENCE.md for Copyright information
"""Database models for the animeu site."""
from flask_login import UserMixin

from animeu.app import db, login_manager

# pylint: disable=too-few-public-methods
class User(db.Model, UserMixin):
    """Table which represents a user of the application."""

    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    username = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    """Load a user object from the database given their ID."""
    return User.query.get(user_id)

class WaifuPickBattle(db.Model):
    """Table which represents a where one girl is chosen as a waifu."""

    __tablename__ = "waifu_battles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    winner_name = db.Column(db.String, index=True, nullable=False)
    loser_name = db.Column(db.String, index=True, nullable=False)

class FavouritedWaifu(db.Model):
    """Table whose rows are an ordered collection of waifus."""

    __tablename__ = "favourited_waifu"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"),
                        index=True, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    character_name = db.Column(db.String, index=True, nullable=False)
    order = db.Column(db.Integer, index=True, nullable=False)
