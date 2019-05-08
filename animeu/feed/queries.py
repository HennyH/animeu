# /animeu/feed/queries.py
#
# Query functions used to populate the feed.
#
# See /LICENCE.md for Copyright information
"""Query functions used to populate the feed."""
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

def query_most_winning_waifus(from_date=None, limit=20):
    """Find the waifus with the most wins in a given date range."""
    appearence_cte = get_battle_appearences_cte()
    query = \
        select([
            appearence_cte.c.name,
            func.sum(appearence_cte.c.was_winner).label("wins"),
            func.sum(appearence_cte.c.was_loser).label("losses"),
        ])
    if from_date:
        query = query.where(appearence_cte.c.date >= from_date)
    query = query\
        .group_by(appearence_cte.c.name)\
        .order_by(func.sum(appearence_cte.c.was_winner).desc())\
        .limit(limit)\
        .alias("sqlalchemy-bug-workaround")
    return db.session.query(query).all()

def query_most_battled_waifus(from_date=None, limit=20):
    """Find the waifus with the most battles in a given date range."""
    appearence_cte = get_battle_appearences_cte()
    query = \
        select([
            appearence_cte.c.name,
            func.sum(appearence_cte.c.was_winner).label("wins"),
            func.sum(appearence_cte.c.was_loser).label("losses"),
        ])
    if from_date:
        query = query.where(appearence_cte.c.date >= from_date)
    query = query\
        .group_by(appearence_cte.c.name)\
        .order_by(func.count().desc())\
        .limit(limit)\
        .alias("sqlalchemy-bug-workaround")
    return db.session.query(query).all()

def query_most_recent_battles(limit=20):
    """Find the most recent battles."""
    return WaifuPickBattle.query\
        .order_by(WaifuPickBattle.date.desc())\
        .limit(limit)\
        .all()
