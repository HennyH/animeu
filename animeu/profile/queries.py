# /animeu/profile/queries.py
#
# Query functions used to populate the profile.
#
# See /LICENCE.md for Copyright information
"""Query functions used to populate the profile."""
from sqlalchemy.sql import select, and_, or_
from animeu.app import db
from animeu.models import FavouritedWaifu, WaifuPickBattle

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

def get_favourite_waifu_list(user_id, limit=10):
    """Return ordered list of favourite waifu."""
    if limit is None:
        raise TypeError("limit cannot be None")
    return FavouritedWaifu.query\
        .filter_by(user_id=user_id)\
        .order_by(FavouritedWaifu.order)\
        .limit(limit)\
        .all()

def get_favourited_waifu_battles(user_id, limit=10):
    """Query the waifus the user has favourited."""
    favourited_waifu_names = \
        select([
            FavouritedWaifu.character_name
        ])\
        .where(FavouritedWaifu.user_id == user_id)
    battles = \
        select([
            WaifuPickBattle
        ])\
        .where(
            or_(
                WaifuPickBattle.winner_name.in_(favourited_waifu_names),
                WaifuPickBattle.loser_name.in_(favourited_waifu_names)
            ))\
        .limit(limit)
    return db.engine.execute(battles).fetchall()
