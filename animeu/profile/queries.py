# /animeu/profile/queries.py
#
# Query functions used to populate the profile.
#
# See /LICENCE.md for Copyright information
"""Query functions used to populate the profile."""
from sqlalchemy.sql import select, and_
from animeu.app import db
from animeu.models import FavouritedWaifu

def query_has_favourited_waifus(user_id, character_names):
    """Return a name -> is favourited map for a given user."""
    matched_names_query = \
        select([
            FavouritedWaifu.character_name
        ])\
        .where(
            and_(
                FavouritedWaifu.character_name.in_(character_names),
                FavouritedWaifu.user_id == user_id
            ))
    matched_names = \
        set(r[0] for r in db.engine.execute(matched_names_query).fetchall())
    return {n: n in matched_names for n in character_names}
