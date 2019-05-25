# /setup.py
#
# Setup file for the animeu module.
#
# See /LICENCE.md for Copyright information
"""Setup file for the animeu module."""
from setuptools import setup, find_packages

setup(
    name="animeu",
    verison="0.0.1",
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "anime-planet-downloader=animeu.spiders.anime_planet_downloader:main",
            "anime-planet-extractor=animeu.spiders.anime_planet_extractor:main",
            "myanimelist-downloader=animeu.spiders.myanimelist_downloader:main",
            "myanimelist-extractor=animeu.spiders.myanimelist_extractor:main",
            "myanimelist-anime-extractor=animeu.spiders.myanimelist_anime_extractor:main",
            "anime-db-create=animeu.spiders.anime_db_generator:create_anime_db_cli",
            "anime-db-match=animeu.spiders.anime_db_generator:match_characters_cli",
            "seed-battles=animeu.seed_battles:main",
            "update-elo-rankings=animeu.elo.elo_leaderboard_updater:update_rankings",
        ]
    }
)
