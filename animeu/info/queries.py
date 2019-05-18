# /animeu/info/queries.py
#
# Query functions used to populate the info page.
#
# See /LICENCE.md for Copyright information
"""Query functions used to populate the info page."""
import json
from sqlalchemy.sql import select, func

from animeu.app import db
from animeu.models import ELORankingCalculation
from animeu.feed.queries import get_battle_appearences_cte

def query_character_win_loss_counts(character_name):
    """Get the number of wins/losses of a character."""
    appearence_cte = get_battle_appearences_cte()
    return db.engine.execute(
        select([
            func.sum(appearence_cte.c.was_winner).label("wins"),
            func.sum(appearence_cte.c.was_loser).label("losses"),
        ])\
        .where(appearence_cte.c.name == character_name)
    ).first()

def query_character_elo(character_name):
    """Get the ELO ranking of a character."""
    elo_calculation = ELORankingCalculation.query\
        .order_by(ELORankingCalculation.id.desc())\
        .first()
    if not elo_calculation:
        return None
    rankings = json.loads(elo_calculation.rankings)
    return rankings.get(character_name)
