# /animeu/elo/elo_leaderboard_updater.py
#
# Task to update the ELO leaderboard.
#
# See /LICENCE.md for Copyright information
"""Task to update the ELO leaderboard."""
import sys
import hashlib
import json
from datetime import datetime

import animeu.elo.elo_algorithim as elo_algorithim
from animeu.app import db
from animeu.models import ELORankingCalculation, WaifuPickBattle

def get_elo_algorithim_hash():
    """Get the hash of the algorithim file."""
    with open(elo_algorithim.__file__, "r") as fileobj:
        md5 = hashlib.md5()
        md5.update(fileobj.read().encode("utf8"))
    return md5.hexdigest()

def update_rankings(progress_callback=None, callback_rate=1000):
    """Update the ELO ranking board."""
    latest_battle = \
        WaifuPickBattle.query.order_by(WaifuPickBattle.date.desc()).first()
    # if there are no battles don't bother updating the rankings.
    if not latest_battle:
        print("elo: no battles found skipping ranking", file=sys.stderr)
        return
    current_algo_hash = get_elo_algorithim_hash()
    latest_ranking_calc = ELORankingCalculation.query\
        .order_by(ELORankingCalculation.date.desc())\
        .first()
    # check we used the same algorithim to update the rankings
    player_to_current_rank = {}
    if latest_ranking_calc:
        if latest_ranking_calc.algorithim_hash == current_algo_hash:
            player_to_current_rank = json.loads(latest_ranking_calc.rankings)
        else:
            latest_ranking_calc = None
            print("elo: ranking algorithim change detected", file=sys.stderr)
    # run the algorithim to determine the new rankings
    new_games_query = WaifuPickBattle.query
    start_battle_id = \
        latest_ranking_calc.latest_battle_id if latest_ranking_calc else 0
    if start_battle_id:
        new_games_query = \
            new_games_query.filter(WaifuPickBattle.id > start_battle_id)
    end_battle_id = new_games_query\
        .order_by(WaifuPickBattle.date.desc())\
        .limit(1)\
        .value(WaifuPickBattle.id) or start_battle_id
    print(f"elo: updating using battles {start_battle_id} - {end_battle_id}",
          file=sys.stderr)
    ordered_games = new_games_query\
        .filter(WaifuPickBattle.id <= end_battle_id)\
        .order_by(WaifuPickBattle.date)\
        .all()
    def _progressable_ordered_games():
        for i, game in enumerate(ordered_games):
            yield game
            if progress_callback:
                if i % callback_rate == 0 or i == len(ordered_games) - 1:
                    progress_callback(i, len(ordered_games))
    if not any(ordered_games):
        progress_callback(1, 1)
    new_rankings = elo_algorithim.calculate_elo_rankings(
        ordered_games=_progressable_ordered_games(),
        player_to_current_rank=player_to_current_rank,
        game_to_winner=lambda g: g.winner_name,
        game_to_loser=lambda g: g.loser_name
    )
    print(json.dumps(new_rankings, indent=2), file=sys.stderr)
    db.session.add(ELORankingCalculation(
        date=datetime.now(),
        latest_battle_id=end_battle_id,
        rankings=json.dumps(new_rankings),
        algorithim_hash=current_algo_hash
    ))
    db.session.commit()
