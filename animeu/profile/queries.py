# /animeu/profile/queries.py
#
# Query functions used to populate the profile.
#
# See /LICENCE.md for Copyright information
"""Query functions used to populate the profile."""
from sqlalchemy.sql import select, func, expression
from animeu.app import db
from animeu.models import WaifuPickBattle

def get_battle_appearences_cte():
    """Create a sqlaclhemy subquery of the battle appearences."""
    wins = select([
        WaifuPickBattle.date,
        WaifuPickBattle.winner_name.label("name"),
        expression.literal_column("1").label("was_winner"),
        expression.literal_column("0").label("was_loser")
    ])
    losses = select([
        WaifuPickBattle.date,
        WaifuPickBattle.loser_name.label("name"),
        expression.literal_column("0").label("was_winner"),
        expression.literal_column("1").label("was_loser")
    ])
    return wins.union_all(losses).cte("battle_appearence")

def query_most_winning_waifus(from_date=None, limit=5):
    """Find the waifus with the most wins in a given date range."""
    appearence_cte = get_battle_appearences_cte()
    query = \
        select([
            appearence_cte.c.name,
            func.count(appearence_cte.c.was_winner).label("wins"),
            func.count(appearence_cte.c.was_winner).label("losses"),
        ])\
        .select_from(appearence_cte)
    if from_date:
        query = query.where(appearence_cte.c.date >= from_date)
    query = query\
        .group_by(appearence_cte.c.name)\
        .order_by(func.count(appearence_cte.c.was_winner).desc())\
        .limit(limit)
    return db.session.query(query).all()
