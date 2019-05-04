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
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    """Load a user object from the database given their ID."""
    return User.query.get(user_id)
