# /animeu/profile/logic.py
#
# Controller related logic for the profile module.
#
# See /LICENCE.md for Copyright information
"""Controller related logic for the profile module."""
from datetime import datetime
from sqlalchemy.sql import and_, select
from animeu.app import db
from animeu.models import FavouritedWaifu

def maybe_get_favourited_waifu(user_id, character_name):
    """Return favourited waifu with a given name of a user if it exists."""
    return FavouritedWaifu.query\
        .filter(
            and_(FavouritedWaifu.user_id == user_id,
                 FavouritedWaifu.character_name == character_name))\
        .first()

def get_next_favourited_waifu_order_for_user(user_id):
    """Return the next favourited waifu order number for a user."""
    query = \
        select([
            FavouritedWaifu.order
        ])\
        .where(FavouritedWaifu.user_id == user_id)\
        .order_by(FavouritedWaifu.order)\
        .limit(1)
    maybe_current_order = db.engine.scalar(query)
    if maybe_current_order is None:
        return 1
    return maybe_current_order + 1


def unfavourite_a_waifu(user_id, character_name):
    """Unfavourite a favourited waifu."""
    maybe_favourited_waifu = maybe_get_favourited_waifu(
        user_id=user_id,
        character_name=character_name
    )
    if maybe_favourited_waifu:
        db.session.delete(maybe_favourited_waifu)
        db.session.commit()
    return maybe_favourited_waifu

def favourite_a_waifu(user_id, character_name):
    """Favourite a waifu by name."""
    # check the user hasn't already favoured the character
    already_favourited_waifu = \
        maybe_get_favourited_waifu(user_id, character_name)
    if already_favourited_waifu:
        return already_favourited_waifu
    order = get_next_favourited_waifu_order_for_user(user_id)
    favourited_waifu = FavouritedWaifu(
        user_id=user_id,
        date=datetime.now(),
        character_name=character_name,
        order=order
    )
    db.session.add(favourited_waifu)
    db.session.commit()
    return favourited_waifu
