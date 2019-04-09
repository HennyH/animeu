# /animeu/spiders/myanimelist_extractor.py
#
# Extractor for the myanimelist pages.
#
# Pages to fix:
#
# https://myanimelist.net/character/38538/Eucliwood_Hellscythe  (description)
# https://myanimelist.net/character/503/Illyasviel_von_Einzbern (tag has text missing, description gets too much)
# https://myanimelist.net/character/82525/Shiro?q=Shiro%20 (tags)
# https://myanimelist.net/character/63/Winry_Rockbell?q=Winry%20Rockbell (tags incorrect)
#
# See /LICENCE.md for Copyright information
"""Extractor for the myanimelist pages."""
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
from operator import itemgetter, methodcaller
from functools import partial
from parsel import Selector, SelectorList
from lxml import etree
from animeu.spiders.myanimelist_downloader import MAL_URL
from animeu.spiders.json_helpers import JSONListStream
from animeu.common.funchelpers import compose
from animeu.common.filehelpers import open_transcoded
from animeu.spiders.xpath_helpers import get_all_text

MALE_PATTERNS = [r"\bhe\b", r"\bhis\b"]

def strip_field_name(text):
    """Strip the field name section from a piece of text.

    For example 'aka: bob' -> 'bob' or 'hair color: green' -> 'green'.
    """
    if not text:
        return None
    return re.sub(r"[^:]+:\s*", "", text)

def select_name(sel):
    """Select the element containing the characters name."""
    # pylint: disable=line-too-long
    return sel.xpath("//div[contains(@class, 'breadcrumb')]/following-sibling::div[1]")

def extract_en_jp_name(sel):
    """Extract the character's full name."""
    name_sel = select_name(sel)
    english_name = name_sel.css("::text").get().strip()
    japanese_name = get_all_text(name_sel.xpath("span")).strip("()")
    return {"en": [english_name], "jp": [japanese_name]}

def extract_info_fields_and_description(sel):
    """Extract the name-value info fields of the character."""
    name_sel = select_name(sel)
    # pylint: disable=line-too-long
    description_text = \
        get_all_text(name_sel.xpath("following-sibling::p/text() | "
                                    "following-sibling::span/text() | "
                                    "following-sibling::i/text() | "
                                    "following-sibling::b/text() | "
                                    "following-sibling::text()"),
                     element_seperator="",
                     element_filter=compose(bool))
    maybe_info_fields_text, *other_text_blocks = \
        re.split(r"\n\s*\n[\s\n]*", description_text)
    info_fields = []
    for line in maybe_info_fields_text.splitlines():
        match = re.match(r"^(?P<key>[^:]{1,30}):\s*(?P<value>.*$)", line)
        if match:
            info_fields.append({"key": match.group("key"),
                                "value": match.group("value")})
        elif info_fields:
            info_fields[-1]["value"] += f"\n {line}"

    description = other_text_blocks[0] if other_text_blocks else None
    return (info_fields, description)

def extract_main_display_picture(sel):
    """Extract the main display picture URL of the character."""
    return sel.xpath("//a[contains(@href, 'pictures')]/img").attrib["src"]

def extract_anime_roles(sel):
    """Extract the animes the character appeared in."""
    anime_table = \
        sel.xpath("//div[text() = 'Animeography']/following-sibling::table[1]")
    roles = []
    for row in anime_table.xpath(".//tr"):
        image_sel, text_sel = row.xpath(".//td")
        picture = image_sel.xpath(".//img").attrib["src"]
        title = get_all_text(text_sel.xpath("./a"))
        role = get_all_text(text_sel.xpath("./div"))
        if re.search(r"main", role, flags=re.IGNORECASE):
            role = "main"
        elif re.search(r"support(ing)?|secondary", role, flags=re.IGNORECASE):
            role = "secondary"
        roles.append({"name": title, "picture": picture, "role": role})
    return roles

def extract_manga_roles(sel):
    """Extract the mangas the character appeared in."""
    anime_table = \
        sel.xpath("//div[text() = 'Mangaography']/following-sibling::table[1]")
    roles = []
    for row in anime_table.xpath(".//tr"):
        image_sel, text_sel = row.xpath(".//td")
        picture = image_sel.xpath(".//img").attrib["src"]
        title = get_all_text(text_sel.xpath("./a"))
        role = get_all_text(text_sel.xpath("./div"))
        if re.search(r"main", role, flags=re.IGNORECASE):
            role = "main"
        elif re.search(r"support(ing)?|secondary", role, flags=re.IGNORECASE):
            role = "secondary"
        roles.append({"name": title, "picture": picture, "role": role})
    return roles

def extract_gallery_pictures(sel):
    """Extract the pictures of the character from the gallery."""
    return sel.xpath("//div[@class = 'picSurround']//img/@src").getall()

def extract_metadata_from_file(filename):
    """Extract the metadata from a file."""
    metadata = {
        "sources": ["myanimelist"],
        "filenames": [filename],
        "names": {"en": [], "jp": []},
        "descriptions": [],
        "nicknames": {"en": [], "jp": []},
        "info_fields": [],
        "rankings": [],
        "tags": [],
        "anime_roles": [],
        "manga_roles": [],
        "pictures": {
            "display": [],
            "gallery": []
        }
    }
    profile_filename = filename
    pictures_filename = filename.replace(".html", ".pictures.html")
    if os.path.exists(profile_filename):
        with open_transcoded(filename, "r") as file_obj:
            profile_sel = parsel.Selector(text=file_obj.read().decode("utf8"))
        metadata["names"] = extract_en_jp_name(profile_sel)
        metadata["pictures"]["display"].append(
            extract_main_display_picture(profile_sel)
        )
        metadata["anime_roles"].extend(extract_anime_roles(profile_sel))
        metadata["manga_roles"].extend(extract_manga_roles(profile_sel))
        info_fields, maybe_description  = \
            extract_info_fields_and_description(profile_sel)
        metadata["info_fields"].extend(info_fields)
        if maybe_description:
            metadata["descriptions"].append(maybe_description)
    if os.path.exists(pictures_filename):
        with open_transcoded(pictures_filename, "r") as file_obj:
            pictures_sel = parsel.Selector(text=file_obj.read().decode("utf8"))
        metadata["pictures"]["gallery"].extend(
            extract_gallery_pictures(pictures_sel)
        )
    return metadata


def test_is_male_character(metadata):
    """Test if a character is male."""
    if metadata["descriptions"] and \
            any(re.search(r"\b(his|he)\b", d, flags=re.I)
                for d in metadata["descriptions"]):
        return True
    for k, v in metadata["info_fields"]:
        if re.search(r"sex", k, flags=re.I) and \
                re.search(r"\b(male|men|man)\b", v, flags=re.I):
            return True
    return False


TEST_FILES = [
    "aHR0cHM6Ly9teWFuaW1lbGlzdC5uZXQvY2hhcmFjdGVyLzM4NTM4L0V1Y2xpd29vZF9IZWxsc2N5dGhl.html",
    "aHR0cHM6Ly9teWFuaW1lbGlzdC5uZXQvY2hhcmFjdGVyLzUwMy9JbGx5YXN2aWVsX3Zvbl9FaW56YmVybg==.html",
    "aHR0cHM6Ly9teWFuaW1lbGlzdC5uZXQvY2hhcmFjdGVyLzgyNTI1L1NoaXJv.html",
    "aHR0cHM6Ly9teWFuaW1lbGlzdC5uZXQvY2hhcmFjdGVyLzYzL1dpbnJ5X1JvY2tiZWxs.html",

    #"aHR0cHM6Ly9teWFuaW1lbGlzdC5uZXQvY2hhcmFjdGVyLzUwMy9JbGx5YXN2aWVsX3Zvbl9FaW56YmVybg==.html"
]

def main(argv=None):
    """Entry point to the myanimelist extractor."""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser("""Extract content from anime pages.""")
    parser.add_argument("--pages-directory",
                        metavar="PAGES",
                        type=str,
                        required=False)
    parser.add_argument("--output",
                        metavar="OUTPUT",
                        type=argparse.FileType("w", encoding="utf8"),
                        default=sys.stdout)
    parser.add_argument("--no-parallel",
                        action="store_true",
                        help="""Disable parallel processing.""")
    result = parser.parse_args(argv)
    filenames = [os.path.join(result.pages_directory, name)
                 for name in os.listdir(result.pages_directory)
                 if not name.endswith(".pictures.html")
                    and name in TEST_FILES]
    with JSONListStream(result.output) as extract_file:
        for metadata in parmap.map(extract_metadata_from_file,
                                   filenames,
                                   pm_pbar=True,
                                   pm_parallel=not result.no_parallel,
                                   pm_chunksize=10):
            if test_is_male_character(metadata):
                print(f"Skipping {metadata['filenames']} as it is a male "
                      f"character.",
                      file=sys.stderr)
                continue
            extract_file.write(metadata)
            result.output.flush()


