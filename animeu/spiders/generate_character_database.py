# /animeu/spiders/generate_character_database.py
#
# Script to generate the character database
#
# See /LICENCE.md for Copyright information
"""Script to generate the character database."""
import sys
import argparse
import re
import json
from functools import partial
from itertools import chain
from operator import itemgetter, methodcaller

import parmap
from fuzzywuzzy import process

from animeu.common.func_helpers import compose
from animeu.spiders.json_helpers import JSONListStream


def unique(*iterables, key=lambda x: x):
    """Merge iterables together keeping only the unique items."""
    seen_keys = set()
    items = chain.from_iterable(iterables)
    for item in items:
        if item is None:
            continue
        item_key = key(item)
        if item_key in seen_keys:
            continue
        seen_keys.add(item_key)
        yield item


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
                                          key=itemgetter("name")))
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


def maybe_match_mal_character(mal_character, ap_characters):
    """Try match a MAL character to an AP character."""
    # we only support anime girls!
    if not mal_character["anime_roles"]:
        return None
    # pylint: disable=broad-except
    try:
        best_ap_match = None
        best_ap_match_score = 0
        for ap_character in ap_characters:
            mal_names = mal_character["names"]["en"]
            ap_names = ap_character["names"]["en"]
            _, _, name_score = max(
                # pylint: disable=line-too-long
                [(n, *(process.extractOne(n, ap_names) or (None, 0))) for n in mal_names],
                key=itemgetter(2)
            )
            if name_score < 90:
                continue
            mal_animes = [a["name"] for a in mal_character["anime_roles"]]
            ap_animes = [a["name"] for a in ap_character["anime_roles"]]
            anime_score = 0
            if mal_animes:
                _, _, anime_score = max(
                    # pylint: disable=line-too-long
                    [(n, *(process.extractOne(n, ap_animes) or (None, 0))) for n in mal_animes],
                    key=itemgetter(2)
                )
            score = anime_score + name_score
            if score > best_ap_match_score:
                best_ap_match_score = score
                best_ap_match = ap_character
        if best_ap_match is not None:
            return merge_character_metadata(mal_character, best_ap_match)
        return None
    except Exception as error:
        print(f"Error occured matching {mal_character}: {error}",
              file=sys.stderr)
        return None


def main(argv=None):
    """Entry point to the anime planet page extractor."""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser("""Extract content from anime pages.""")
    parser.add_argument("--myanimelist-extract",
                        metavar="MAL_EXTRACT",
                        type=str,
                        required=True)
    parser.add_argument("--anime-planet-extract",
                        metavar="ANIME_PLANET_EXTRACT",
                        type=str,
                        required=True)
    parser.add_argument("--output",
                        metavar="OUTPUT",
                        type=argparse.FileType("w"),
                        default=sys.stdout)
    result = parser.parse_args(argv)
    with open(result.myanimelist_extract, "r") as mal_fileobj:
        mal_json = json.load(mal_fileobj)
    with open(result.anime_planet_extract, "r") as ap_fileobj:
        ap_json = json.load(ap_fileobj)
    with JSONListStream(result.output) as json_stream:
        for maybe_match in parmap.map(maybe_match_mal_character,
                                      mal_json,
                                      ap_json,
                                      pm_pbar=True):
            if maybe_match is not None:
                json_stream.write(maybe_match)
