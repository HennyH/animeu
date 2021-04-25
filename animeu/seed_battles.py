# /animeu/seed_battles.py
#
# CLI app to seed battles into the database.
#
# See /LICENCE.md for Copyright information
"""CLI app to seed battles into the database."""
import sys
import os
import argparse
import random
import json
from datetime import datetime
from functools import partial

from tqdm import tqdm

from animeu.data_loader import load_character_data
from animeu.app import db
from animeu.models import User, WaifuPickBattle
from animeu.auth.logic import hash_password

def get_seeding_user():
    """Add the seeding user to the database."""
    user = User(email="seedy-seeder-mcseeder@gmail.com",
                username="seedymcguee",
                password_hash=hash_password("iamtheseeder"),
                is_admin=False)
    existing_user = User.query.filter_by(email=user.email).first()
    if existing_user:
        return existing_user
    db.session.add(user)
    db.session.commit()
    return user

def get_character_ranking(character, name):
    """Get a particular ranking of a character."""
    value = [r for r in character["rankings"] if r["name"] == name][0]["value"]
    try:
        return float(value)
    except ValueError:
        return 1

def get_character_ratio_ranking(character, numerator, denominator):
    """Get a particular ratio base ranking of a character."""
    numerator_value = get_character_ranking(character, numerator)
    denominator_value = get_character_ranking(character, denominator)
    return numerator_value / denominator_value

def get_max_ranking(characters, name):
    """Get the maximum value for a ranking."""
    return max(map(partial(get_character_ranking, name=name), characters))

def get_max_ratio_ranking(characters, numerator, denominator):
    """Get the maximum ratio value for a ranking."""
    get_ratio = partial(get_character_ratio_ranking,
                        numerator=numerator,
                        denominator=denominator)
    return max(map(get_ratio, characters))

def get_normalized_character_ranking(characters, character, name):
    """Get and normalize a ranking so it is between 0 - 1."""
    ranking = get_character_ranking(character, name)
    max_ranking = get_max_ranking(characters, name)
    return ranking / max_ranking

# pylint: disable=line-too-long
def get_normalized_character_ratio(characters, character, numerator, denominator):
    """Get and normalize a ratio ranking so it is between 0 - 1."""
    ranking = get_character_ratio_ranking(character, numerator, denominator)
    max_ranking = get_max_ratio_ranking(characters, numerator, denominator)
    return ranking / max_ranking

def get_ranking_functions(characters):
    """Get a list of ranking functions to use."""
    return [
        partial(get_normalized_character_ratio,
                characters,
                numerator="top_loved",
                denominator="top_hated"),
        partial(get_normalized_character_ratio,
                characters,
                numerator="heart_on",
                denominator="heart_off"),
        partial(get_normalized_character_ranking,
                characters,
                name="heart_on"),
        partial(get_normalized_character_ranking,
                characters,
                name="top_loved")
    ]

def seed_battles(iterations, progress_callback=None, callback_rate=1000):
    """Seed the database with N iterations of battles."""
    user = get_seeding_user()
    characters = load_character_data()
    ranking_functions = get_ranking_functions(characters)

    # pylint: disable=unused-variable
    for iteration in tqdm(range(iterations)):
        left = random.choice(characters)
        right = random.choice(characters)
        ranking_func = random.choice(ranking_functions)
        left_win_prob = random.uniform(
            # by default there is a 50/50 chance
            0.5,
            # add on at most 40% odds of winning
            0.5 + (0.4 * (ranking_func(left) - ranking_func(right)))
        )
        if random.random() >= left_win_prob:
            winner = left
            loser = right
        else:
            winner = right
            loser = left
        db.session.add(WaifuPickBattle(
            user_id=user.id,
            date=datetime.now(),
            winner_name=winner["names"]["en"][0],
            loser_name=loser["names"]["en"][0]
        ))
        if progress_callback:
            if iteration % callback_rate == 0 or iteration == iterations - 1:
                progress_callback(iteration, iterations)
    db.session.commit()

def main(argv=None):
    """Entry point to the seeder program."""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser("""Database battle seeder.""")
    parser.add_argument("--battles",
                        metavar="BATTLES",
                        type=int,
                        default=50000)
    parser.add_argument("--log", action="store_true")
    result = parser.parse_args(argv)
    if result.log:
        os.environ["SQLALCHEMY_ECHO"] = "True"
    seed_battles(result.iterations)

if __name__ == "__main__":
    main()
