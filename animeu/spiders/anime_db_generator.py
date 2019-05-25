# /animeu/spiders/anime_db_generator.py
#
# Generate an anime database from an anime extract.
#
# See /LICENCE.md for Copyright information
"""Generate an anime database from an anime extract."""
import sys
import argparse
import json
import re
from string import punctuation
from itertools import chain, product
from operator import itemgetter, methodcaller
from functools import reduce, partial

from pkg_resources import resource_string
from apsw import Connection
from Levenshtein import jaro
from tqdm import tqdm

from animeu.common.func_helpers import compose
from animeu.common.file_helpers import JSONListStream, open_transcoded

SCHEMA_SQL = resource_string(__name__, "schema.sql").decode()
MATCH_SQL = resource_string(__name__, "match.sql").decode()
BLACKLISTED_TAG_RES = [r"child(ren)?", r"elementary\s+school",
                       r"underage", r"^animals?$", r"^elderly$",
                       r"^bab(y|ies)$", r"^fairies$"]

def unique(*iterables, key=lambda x: x):
    """Merge iterables together keeping only the unique items."""
    seen_key_to_item = {}
    items = chain.from_iterable(iterables)
    for item in items:
        if item is None:
            continue
        item_key = key(item)
        if item_key in seen_key_to_item and \
                len(item) < len(seen_key_to_item.get(item_key)):
            continue
        seen_key_to_item[item_key] = item
    return seen_key_to_item.values()


def merge_character_metadata(left, right):
    """Merge together two anime character profiles."""
    case_insensitive = compose(partial(re.sub, r"\s", ""),
                               methodcaller("lower"))
    metadata = {}
    metadata["sources"] = [*left["sources"], *right["sources"]]
    metadata["filenames"] = [*left["filenames"], *right["filenames"]]
    metadata["names"] = {
        "en": list(unique(left["names"]["en"],
                          right["names"]["en"],
                          key=case_insensitive)),
        "jp": list(unique(left["names"]["jp"],
                          right["names"]["jp"],
                          key=case_insensitive))
    }
    metadata["descriptions"] = list(unique(left["descriptions"],
                                           right["descriptions"],
                                           key=case_insensitive))
    metadata["nicknames"] = {
        "en": list(unique(left["nicknames"]["en"],
                          right["nicknames"]["en"],
                          key=case_insensitive)),
        "jp": list(unique(left["nicknames"]["jp"],
                          right["nicknames"]["jp"],
                          key=case_insensitive))
    }
    metadata["info_fields"] = list(unique(left["info_fields"],
                                          right["info_fields"],
                                          key=itemgetter("key")))
    metadata["rankings"] = list(unique(left["rankings"],
                                       right["rankings"],
                                       key=itemgetter("name")))
    metadata["tags"] = list(unique(left["tags"],
                                   right["tags"],
                                   key=case_insensitive))
    metadata["anime_roles"] = list(unique(left["anime_roles"],
                                          right["anime_roles"],
                                          key=compose(case_insensitive,
                                                      itemgetter("name"))))
    metadata["manga_roles"] = list(unique(left["manga_roles"],
                                          right["manga_roles"],
                                          key=compose(case_insensitive,
                                                      itemgetter("name"))))
    metadata["pictures"] = {
        "display": list(unique(left["pictures"]["display"],
                               right["pictures"]["display"])),
        "gallery": list(unique(left["pictures"]["gallery"],
                               right["pictures"]["gallery"]))
    }
    return metadata

def normalize_anime_name(anime_name):
    """Normalize an anime name for loose matching."""
    anime_name = anime_name.translate(str.maketrans("", "", punctuation))
    anime_name = anime_name.lower()
    anime_name = re.sub(r"\s", "", anime_name)
    return anime_name.strip()

def normalize_character_name(character_name):
    """Normalize a character name for matching."""
    character_name = character_name.translate(str.maketrans("", "", punctuation))
    character_name = character_name.lower()
    character_name = re.sub(r"\s+", "", character_name)
    return character_name.strip()

def is_sensitive_metadata(metadata):
    """Test if a metadata contains sensitive content."""
    tags = metadata.get("tags", [])
    for tag in tags:
        for pattern in BLACKLISTED_TAG_RES:
            if re.search(pattern, tag, flags=re.IGNORECASE):
                return True
    return False

def create_anime_db(database, anime_extract):
    """Create an anime database from an anime extract."""
    with open_transcoded(anime_extract, "r", errors="ignore") as anime_fileobj:
        anime_json = json.loads(anime_fileobj.read().decode("utf8"))
    with Connection(database) as connection:
        connection.createscalarfunction("lv_jaro",
                                        jaro,
                                        numargs=2,
                                        deterministic=True)
        cursor = connection.cursor()
        cursor.execute(SCHEMA_SQL)
        for anime_id, anime in enumerate(tqdm(anime_json), start=1):
            cursor.execute("insert into anime values (:anime_id)",
                           {"anime_id": anime_id})
            for name in anime["names"]:
                cursor.execute(
                    "insert into anime_name (is_primary, anime_id, "
                    "anime_name, normalized_anime_name) values (:is_primary, "
                    ":anime_id, :anime_name, :normalized_anime_name)",
                    {"is_primary": name["is_primary"],
                     "anime_id": anime_id,
                     "anime_name": name["name"],
                     "normalized_anime_name": (
                         normalize_anime_name(name["name"])
                     )
                    })
            for character in anime["characters"]:
                cursor.execute(
                    "insert into character_name (anime_id, character_name, "
                    "normalized_character_name) values (:anime_id, "
                    ":character_name, :normalized_character_name)",
                    {"anime_id": anime_id,
                     "character_name": character["name"],
                     "normalized_character_name": (
                         normalize_character_name(character["name"])
                     )
                    })
        cursor.execute("REINDEX")

# pylint: disable=too-many-locals
def match_character_extracts(anime_database, character_extracts):
    """Match and merge characters using an anime database."""
    next_reference_id = 1
    reference_id_to_character = {}
    with Connection(anime_database) as connection:
        connection.createscalarfunction("lv_jaro",
                                        jaro,
                                        numargs=2,
                                        deterministic=True)
        cursor = connection.cursor()
        cursor.execute("delete from unmatched_character")
        for filename in tqdm(character_extracts):
            # pylint: disable=line-too-long
            with open_transcoded(filename, "r", errors="ignore") as character_fileobj:
                character_json = json.loads(character_fileobj.read().decode("utf8"))
            for character in tqdm(character_json):
                reference_id = next_reference_id
                reference_id_to_character[reference_id] = character
                character_names = \
                    list(chain.from_iterable(character["names"].values()))
                anime_names = [a["name"] for a in character["anime_roles"]]
                for character_name, anime_name in product(character_names,
                                                          anime_names):
                    cursor.execute("insert into unmatched_character ("
                                   "character_name, normalized_character_name,"
                                   "anime_name, normalized_anime_name, "
                                   "reference_id) values (?, ?, ?, ?, ?)",
                                   (
                                       character_name,
                                       normalize_character_name(character_name),
                                       anime_name,
                                       normalize_anime_name(anime_name),
                                       reference_id
                                   ))
                next_reference_id += 1
    cursor.execute("REINDEX")
    for (reference_id_csv,) in cursor.execute(MATCH_SQL):
        reference_ids = list(map(int, reference_id_csv.split(",")))
        characters = map(reference_id_to_character.get, reference_ids)
        merged_character = reduce(merge_character_metadata, characters)
        if is_sensitive_metadata(merged_character):
            print(f"Skipping character {merged_character['names']['en']} "
                  f"due to sensitive metadata.",
                  file=sys.stderr)
            continue
        yield merged_character

def match_characters_cli(argv=None):
    """Entry point to the anime database character matcher."""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser("""Generate an anime database.""")
    parser.add_argument("--database",
                        metavar="EXTRACT",
                        type=str,
                        required=True)
    parser.add_argument("--anime-extract",
                        metavar="EXTRACT",
                        type=str,
                        required=True)
    parser.add_argument("--character-extracts",
                        metavar="DATABASE",
                        type=str,
                        nargs="+",
                        required=True)
    parser.add_argument("--output",
                        metavar="OUTPUT",
                        type=argparse.FileType("w", encoding="utf8"),
                        default=sys.stdout)
    result = parser.parse_args(argv)
    create_anime_db(result.database, result.anime_extract)
    with JSONListStream(result.output) as json_stream:
        for character in match_character_extracts(result.database,
                                                  result.character_extracts):
            json_stream.write(character)

def create_anime_db_cli(argv=None):
    """Entry point to the anime database generator."""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser("""Generate an anime database.""")
    parser.add_argument("--database",
                        metavar="DATABASE",
                        type=str,
                        required=True)
    parser.add_argument("--anime-extract",
                        metavar="EXTRACT",
                        type=str,
                        required=True)
    result = parser.parse_args(argv)
    create_anime_db(result.database, result.anime_extract)
