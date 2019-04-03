# /animeu/spiders/page_extractor.py
#
# Metadata extractor for anime planet pages.
#
# See /LICENCE.md for Copyright information
"""Metadata extractor for anime planet pages."""
import os
import sys
import argparse
import parsel
import re
import urllib.parse
import requests
import base64
import json
import parmap
from parsel import Selector, SelectorList
from animeu.spiders.page_downloader import ANIME_PLANET_URL
from animeu.spiders.json_helpers import JSONListStream

BLACKLISTED_TAG_RES = [r"child(ren)?", r"elementary\s+school", r"underage"]

def optional(func, default=None):
    """Wrap a function which could fail."""
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as error:
            print(f"{func}(args={args}, kwargs={kwargs}) encountered error: "
                  f"{error}",
                  file=sys.stderr)
            return default
    return wrapped

def normalize_whitespace(text):
    """Normalize whitespace and change ```&nbsp;``` to a normal space."""
    text = text.replace(u"\xa0", u" ")
    text = text.replace(u"\u2019", u"'")
    text = text.replace(u"\u00c2", u" ")
    text = re.sub(r"[^\S\n]+", " ", text)
    text = text.strip()
    return text

def get_all_text(sel,
                 element_seperator="\n",
                 element_filter=lambda x: True,
                 element_transform=lambda x: x):
    """Get all the text in the selector."""
    if not isinstance(sel, (Selector, SelectorList)):
        raise TypeError("""Expected either Selector or SelectorList.""")
    # The trouble here is that we may be passing in either a list of or single
    # Selector and we need to peek into the `_expr` property to properly
    # deal with `/text()` nodes so we normalize both types of arguments
    # into a SelectorList.
    if isinstance(sel, Selector):
        selectors = SelectorList([sel])
    else:
        selectors = sel

    text_fragments = []
    for maybe_text_selector in selectors:
        # text elements have no other elements 'below' them hence
        # the `*::text()` expression used below to get all text within
        # a node won't work here! Instead we use `get()` to get the
        # non-nested content of a single node.
        #
        # pylint: disable=protected-access
        if hasattr(maybe_text_selector, "_expr") and \
                maybe_text_selector._expr is not None and \
                maybe_text_selector._expr.endswith("text()"):
            text_fragments.append(maybe_text_selector.get())
        else:
            text_selectors = maybe_text_selector.css("*::text")
            text_fragments.extend(text_selectors.extract())

    element_seperator = "" if element_seperator is None else element_seperator
    text_fragments = list(map(element_transform, text_fragments))
    text_fragments = list(filter(element_filter, text_fragments))
    text = element_seperator.join(text_fragments)
    return normalize_whitespace(text)

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

@optional
def extract_name(sel):
    """Extract the character's full name."""
    return get_all_text(sel.xpath("//h1[@itemprop = 'name']"))

@optional
def extract_nickname(sel):
    """Extract the character's nickname."""
    return strip_field_name(get_all_text(sel.xpath("//h2[@class = 'aka']")))

@optional
def extract_hair_color(sel):
    """Extract the character's hair color."""
    stats_sel = select_basic_stats_section(sel)
    return strip_field_name(
        get_all_text(stats_sel.xpath("div[re:test(., 'hair color', 'i')]"))
    )

@optional
def extract_top_loved_rank(sel):
    """Extract the character's top loved rank."""
    stats_sel = select_basic_stats_section(sel)
    return re.sub(
        r"[^\d]|#",
        "",
        get_all_text(stats_sel.xpath("div/a[re:test(@href, 'top-loved')]"))
    )

@optional
def extract_top_hated_rank(sel):
    """Extract the character's top loved rank."""
    stats_sel = select_basic_stats_section(sel)
    return re.sub(
        r"[^\d]|#",
        "",
        get_all_text(stats_sel.xpath("div/a[re:test(@href, 'top-hated')]"))
    )

@optional
def extract_heart_on_number(sel):
    """Extract the number of heart on emojis the character has recieved."""
    return re.sub(r"[^\d]|#",
                  "",
                  get_all_text(sel.xpath("//h3[./span[@class = 'heartOn']]")))

@optional
def extract_heart_off_number(sel):
    """Extract the number of heart off emojis the character has recieved."""
    return re.sub(r"[^\d]|#",
                  "",
                  get_all_text(sel.xpath("//h3[./span[@class = 'heartOff']]")))

@optional
def extract_tags(sel):
    """Extract the tags associated with the character."""
    return list(map(get_all_text, sel.xpath("//div[@class = 'tags']/ul/li/a")))

@optional
def extract_anime_roles(sel):
    """Extract the anime roles the character has appeared in."""
    anime_roles_table_sel = \
        sel.xpath("//h3[text() = 'Anime Roles']/following-sibling::table[1]")
    anime_roles = []
    for row in anime_roles_table_sel.xpath("//tr"):
        anime, role, *_ = list(map(get_all_text, row.xpath("td")))
        anime_roles.append({"name": anime, "role": role})
    return anime_roles

@optional
def extract_manga_roles(sel):
    """Extract the manga roles the character has appeared in."""
    manga_roles_table_sel = \
        sel.xpath("//h3[text() = 'Manga Roles']/following-sibling::table[1]")
    manga_roles = []
    for row in manga_roles_table_sel.xpath("//tr"):
        manga, role, *_ = list(map(get_all_text, row.xpath("td")))
        manga_roles.append({"name": manga, "role": role})
    return manga_roles

@optional
def extract_display_picture(sel):
    """Extract the display picture for the character."""
    relative_src = sel.xpath("//img[@itemprop = 'image']").attrib["src"]
    return urllib.parse.urljoin(ANIME_PLANET_URL, relative_src)

@optional
def extract_description(sel):
    """Extract the description of the character."""
    return get_all_text(sel.xpath("//div[@itemprop = 'description']"))

def extract_metadata_from_file(filename):
    """Extract the metadata from a file."""
    with open(filename, "r", errors="ignore") as file_obj:
        text = file_obj.read()
    sel = parsel.Selector(text=text)
    return {
        "filename": os.path.basename(filename),
        "name": extract_name(sel),
        "nickname": extract_nickname(sel),
        "hair_color": extract_hair_color(sel),
        "top_loved_rank": extract_top_loved_rank(sel),
        "top_hated_rank": extract_top_hated_rank(sel),
        "heart_on_number": extract_heart_on_number(sel),
        "heart_off_number": extract_heart_off_number(sel),
        "tags": extract_tags(sel) or [],
        "anime_roles": extract_anime_roles(sel) or [],
        "manga_roles": extract_manga_roles(sel) or [],
        "picture": extract_display_picture(sel),
        "description": extract_description(sel)
    }

def is_sensitive_metadata(metadata):
    """Test if a metadata contains sensitive content."""
    tags = metadata.get("tags", [])
    for tag in tags:
        for pattern in BLACKLISTED_TAG_RES:
            if re.search(pattern, tag, flags=re.IGNORECASE):
                return True

def main(argv=None):
    """Entry point to the anime planet page extractor."""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser("""Extract content from anime pages.""")
    parser.add_argument("--pages-directory",
                        metavar="PAGES",
                        type=str,
                        required=False)
    parser.add_argument("--output",
                        metavar="OUTPUT",
                        type=argparse.FileType("w"),
                        default=sys.stdout)
    parser.add_argument("--no-parallel",
                        action="store_true",
                        help="""Disable parallel processing.""")
    result = parser.parse_args(argv)
    filenames = [os.path.join(result.pages_directory, name)
                 for name in os.listdir(result.pages_directory)]
    with JSONListStream(result.output) as extract_file:
        for metadata in parmap.map(extract_metadata_from_file,
                                   filenames,
                                   pm_pbar=True,
                                   pm_parallel=not result.no_parallel,
                                   pm_chunksize=10):
            if is_sensitive_metadata(metadata):
                print(f"Skipping {metadata['filename']} "
                      f"due to sensitive content.",
                      file=sys.stderr)
                continue
            extract_file.write(metadata)
            result.output.flush()
