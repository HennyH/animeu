# /animeu/auth/logic.py
#
# Controller related logic for the auth module.
#
# See /LICENCE.md for Copyright information
"""Controller related logic for the auth module."""
from werkzeug.security import generate_password_hash, check_password_hash

from animeu.models import User

def hash_password(plaintext):
    """Hash a password."""
    return generate_password_hash(plaintext)

def check_password(plaintext, a_password_hash):
    """Check if a plaintext value matches a hashed value."""
    return check_password_hash(a_password_hash, plaintext)

def maybe_find_user(email, password=None):
    """Search the database for a user."""
    if email is None:
        return None
    maybe_user = User.query.filter_by(email=email).first()
    if maybe_user is not None and (
                password is None or \
                check_password(password, maybe_user.password_hash)
    ):
        return maybe_user
    return None
