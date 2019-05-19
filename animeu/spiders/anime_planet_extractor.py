# /animeu/spiders/page_extractor.py
#
# Metadata extractor for anime planet pages.
#
# See /LICENCE.md for Copyright information
"""Metadata extractor for anime planet pages."""
import os
import sys
import re
import urllib.parse
import json
from functools import partial

import argparse
import parmap
import parsel

from animeu.spiders.anime_planet_downloader import ANIME_PLANET_URL
from animeu.spiders.json_helpers import JSONListStream
from animeu.spiders.xpath_helpers import get_all_text

def strip_field_name(text):
    """Strip the field name section from a piece of text.

    For example 'aka: bob' -> 'bob' or 'hair color: green' -> 'green'.
    """
    if not text:
        return None
    return re.sub(r"[^:]+:\s*", "", text)

def select_basic_stats_section(sel):
    """Select the section which contains basic stats such as hair color."""
    return sel.xpath("//section[contains(@class, 'entryBar')]")

def extract_names(sel):
    """Extract the character's full name."""
    return [get_all_text(sel.xpath("//h1[@itemprop = 'name']"))]

def extract_nicknames(sel):
    """Extract the character's nickname."""
    return [strip_field_name(get_all_text(sel.xpath("//h2[@class = 'aka']")))]

def extract_info_fields(sel):
    """Extract the character's hair color."""
    stats_sel = select_basic_stats_section(sel)
    return [
        {"key": "Hair Color", "value": strip_field_name(
            get_all_text(stats_sel.xpath("div[re:test(., 'hair color', 'i')]"))
        )}
    ]

def extract_top_loved_rank(sel):
    """Extract the character's top loved rank."""
    stats_sel = select_basic_stats_section(sel)
    return re.sub(
        r"[^\d]|#",
        "",
        get_all_text(stats_sel.xpath("div/a[re:test(@href, 'top-loved')]"))
    )

def extract_top_hated_rank(sel):
    """Extract the character's top loved rank."""
    stats_sel = select_basic_stats_section(sel)
    return re.sub(
        r"[^\d]|#",
        "",
        get_all_text(stats_sel.xpath("div/a[re:test(@href, 'top-hated')]"))
    )

def extract_heart_on_number(sel):
    """Extract the number of heart on emojis the character has recieved."""
    return re.sub(r"[^\d]|#",
                  "",
                  get_all_text(sel.xpath("//h3[./span[@class = 'heartOn']]")))

def extract_heart_off_number(sel):
    """Extract the number of heart off emojis the character has recieved."""
    return re.sub(r"[^\d]|#",
                  "",
                  get_all_text(sel.xpath("//h3[./span[@class = 'heartOff']]")))

def extract_tags(sel):
    """Extract the tags associated with the character."""
    return list(map(get_all_text, sel.xpath("//div[@class = 'tags']/ul/li/a")))

def extract_anime_roles(sel):
    """Extract the anime roles the character has appeared in."""
    anime_roles_table_sel = \
        sel.xpath("//h3[text() = 'Anime Roles']/following-sibling::table[1]")
    anime_roles = []
    for row in anime_roles_table_sel.xpath("//tr"):
        anime, role, *_ = list(map(get_all_text, row.xpath("td")))
        anime_roles.append({"name": anime, "role": role})
    return anime_roles

def extract_manga_roles(sel):
    """Extract the manga roles the character has appeared in."""
    manga_roles_table_sel = \
        sel.xpath("//h3[text() = 'Manga Roles']/following-sibling::table[1]")
    manga_roles = []
    for row in manga_roles_table_sel.xpath("//tr"):
        manga, role, *_ = list(map(get_all_text, row.xpath("td")))
        manga_roles.append({"name": manga, "role": role})
    return manga_roles

def extract_display_pictures(sel):
    """Extract the display picture for the character."""
    relative_src = sel.xpath("//img[@itemprop = 'image']").attrib["src"]
    return [urllib.parse.urljoin(ANIME_PLANET_URL, relative_src)]

def extract_descriptions(sel):
    """Extract the description of the character."""
    return [get_all_text(sel.xpath("//div[@itemprop = 'description']"))]

def optional(func, filename=None, default=None):
    """Wrap a function which could fail."""
    def wrapped(*args, **kwargs):
        # pylint: disable=broad-except
        try:
            return func(*args, **kwargs)
        except Exception as error:
            print(f"file={filename} {func}(args={args}, kwargs={kwargs}) "
                  f"encountered error: {error}",
                  file=sys.stderr)
            return default
    return wrapped


def extract_metadata_from_file(filename):
    """Extract the metadata from a file."""
    with open(filename, "r", errors="ignore") as file_obj:
        text = file_obj.read()
    sel = parsel.Selector(text=text)
    def list_optional(func, sel):
        return list(filter(bool,
                           optional(func, filename=filename, default=[])(sel)))
    return {
        "sources": ["anime-planet"],
        "filenames": [os.path.basename(filename)],
        "names": {
            "en": list_optional(extract_names, sel),
            "jp": []
        },
        "descriptions": list_optional(extract_descriptions, sel),
        "nicknames": {
            "en": list_optional(extract_nicknames, sel),
            "jp": []
        },
        "info_fields": list_optional(extract_info_fields, sel),
        "rankings": [
            {"name": "top_loved", "value": extract_top_loved_rank(sel)},
            {"name": "top_hated", "value": extract_top_hated_rank(sel)},
            {"name": "heart_on", "value": extract_heart_on_number(sel)},
            {"name": "heart_off", "value": extract_heart_off_number(sel)},
        ],
        "tags": list_optional(extract_tags, sel),
        "anime_roles": list_optional(extract_anime_roles, sel),
        "manga_roles": list_optional(extract_manga_roles, sel),
        "pictures": {
            "display": [],
            "gallery": list_optional(extract_display_pictures, sel)
        }
    }

def main(argv=None):
    """Entry point to the anime planet page extractor."""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser("""Extract content from anime pages.""")
    parser.add_argument("--pages-directory",
                        metavar="PAGES",
                        type=str,
                        required=False)
    parser.add_argument("--output",
                        metavar="MANIFEST",
                        type=argparse.FileType("w"),
                        default=sys.stdout)
    parser.add_argument("--no-parallel",
                        action="store_true",
                        help="""Disable parallel processing.""")
    result = parser.parse_args(argv)
    basenames = os.listdir(result.pages_directory)
    filenames = \
        list(map(partial(os.path.join, result.pages_directory), basenames))
    with JSONListStream(result.output) as extract_file:
        for metadata in parmap.map(extract_metadata_from_file,
                                   filenames,
                                   pm_pbar=True,
                                   pm_parallel=not result.no_parallel,
                                   pm_chunksize=10):
            extract_file.write(metadata)
            result.output.flush()
