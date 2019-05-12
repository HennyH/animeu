# /animeu/seed_battles.py
#
# CLI app to seed battles into the database.
#
# See /LICENCE.md for Copyright information
"""CLI app to seed battles into the database."""
import sys
import argparse
import random
from datetime import datetime

from animeu.data_loader import load_character_data
from animeu.app import db
from animeu.models import User, WaifuPickBattle
from animeu.auth.logic import hash_password

def get_seeding_user():
    """Add the seeding user to the database."""
    user = User(email="seedy-seeder-mcseeder@gmail.com",
                username="seedymcguee",
                password_hash=hash_password("seeder"),
                is_admin=False)
    existing_user = User.query.filter_by(email=user.email).first()
    if existing_user:
        return existing_user
    db.session.add(user)
    db.session.commit()
    return user


def get_character_heart_on_off_ratio(character):
    """Get the heart on/off ratio for a character."""
    heart_on = \
        [r for r in character["rankings"] if r["name"] == "heart_on"][0]
    heart_off = \
        [r for r in character["rankings"] if r["name"] == "heart_off"][0]
    return float(heart_on["value"]) / float(heart_off["value"])

def normalize_heart_on_off_ratio(ratio, max_ratio):
    """Normalize a heart on/off ratio to between 0 - 1."""
    return ratio / max_ratio

def main(argv=None):
    """Entry point to the seeder program."""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser("""Database battle seeder.""")
    parser.add_argument("--battles",
                        metavar="BATTLES",
                        type=int,
                        default=50000)
    result = parser.parse_args(argv)
    user = get_seeding_user()
    characters = load_character_data()
    max_heart_on_off_ratio = \
        max(map(get_character_heart_on_off_ratio, characters))
    # pylint: disable=unused-variable
    for iteration in range(result.battles):
        left = random.choice(characters)
        right = random.choice(characters)
        left_heart_on_off_ratio = normalize_heart_on_off_ratio(
            get_character_heart_on_off_ratio(left),
            max_heart_on_off_ratio
        )
        right_heart_on_off_ratio = normalize_heart_on_off_ratio(
            get_character_heart_on_off_ratio(right),
            max_heart_on_off_ratio
        )
        left_win_prob = random.uniform(
            0.5,
            0.5 + (0.4 * (left_heart_on_off_ratio - right_heart_on_off_ratio))
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
    db.session.commit()

if __name__ == "__main__":
    main()
