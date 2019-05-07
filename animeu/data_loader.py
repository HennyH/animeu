# /animeu/data_loader.py
#
# Helper function to load the character data.
#
# See /LICENCE.md for Copyright information
"""Helper function to load the character data."""

import os
import tempfile
import subprocess
import json
from functools import lru_cache

def temp_fix_picutres(character):
    """Remove the 23x32 gallery images from a character."""
    character["pictures"]["gallery"] = \
        [p for p in character["pictures"]["gallery"]
         if "23x32" not in p and "questionmark" not in p]
    return character

@lru_cache(maxsize=1)
def load_character_data():
    """Load the character data from DATA_FILE or DATA_GOOGLE_DRIVE_ID."""
    maybe_data_file = os.environ.get("DATA_FILE")
    maybe_gdrive_file_id = os.environ.get("DATA_GOOGLE_DRIVE_ID")
    if not maybe_data_file and not maybe_gdrive_file_id:
        raise Exception("Either DATA_FILE or DATA_GOOGLE_DRIVE_ID "
                        "have not been set.")
    if maybe_data_file:
        with open(maybe_data_file, "rb") as fileobj:
            json_bytes = fileobj.read()
    else:
        temp_filename = os.path.join(tempfile.gettempdir(), "characters.json")
        subprocess.run(
            [
                "youtube-dl",
                f"https://drive.google.com/open?id={maybe_gdrive_file_id}",
                "--output",
                temp_filename
            ],
            check=True
        )
        with open(temp_filename, "rb") as fileobj:
            json_bytes = fileobj.read()
    characters = json.loads(json_bytes, encoding="utf8")
    for character in characters:
        temp_fix_picutres(character)
    return characters

@lru_cache(maxsize=1)
def load_name_to_character_map():
    """Load a map from name to character."""
    name_to_character = {}
    for character in load_character_data():
        for name in character["names"]["en"]:
            name_to_character[name] = character
        for name in character["names"]["jp"]:
            name_to_character[name] = character
    return name_to_character

def get_character_by_name(en_name):
    """Get a character by their name."""
    return load_name_to_character_map()[en_name]
