# /animeu/spiders/myanimelist_extractor.py
#
# Extractor for the myanimelist pages.
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
from animeu.spiders.myanimelist_downloader import MAL_URL
from animeu.spiders.json_helpers import JSONListStream
from animeu.common.funchelpers import compose
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

def extract_name(sel):
    """Extract the character's full name."""
    name_sel = select_name(sel)
    english_name = name_sel.css("::text").get().strip()
    japanese_name = get_all_text(name_sel.xpath("span")).strip("()")
    return {"en": english_name, "jp": japanese_name}

def extract_info_fields_and_description(sel):
    """Extract the key-value info fields of the character."""
    name_sel = select_name(sel)
    # pylint: disable=line-too-long
    description_lines = \
        get_all_text(name_sel.xpath("../text()"),
                     element_seperator="",
                     element_filter=bool).splitlines()
    info_fields = []
    description = ""
    line_iterator = iter(description_lines)
    for line in line_iterator:
        match = re.match(r"^(?P<key>[^:]{1,30}):\s*(?P<value>.*$)", line)
        if not match:
            break
        info_fields.append({"key": match.group("key"),
                            "value": match.group("value")})
    for line in line_iterator:
        description += "\n" + line
    return {
        "info_fields": info_fields,
        "description": description or None
    }

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
        "filename": filename,
        "name": {"en": None, "jp": None},
        "info_fields": [],
        "description": None,
        "anime_roles": [],
        "manga_roles": [],
        "pictures": []
    }
    profile_filename = filename
    pictures_filename = filename.replace(".html", ".pictures.html")
    if os.path.exists(profile_filename):
        with open(profile_filename, "r", errors="ignore") as file_obj:
            profile_sel = parsel.Selector(text=file_obj.read())
        metadata.update({
            "name": extract_name(profile_sel),
            "main_picture": extract_main_display_picture(profile_sel),
            "anime_roles": extract_anime_roles(profile_sel),
            "manga_roles": extract_manga_roles(profile_sel),
            **extract_info_fields_and_description(profile_sel)
        })
    if os.path.exists(pictures_filename):
        with open(pictures_filename, "r", errors="ignore") as file_obj:
            pictures_sel = parsel.Selector(text=file_obj.read())
        metadata.update({
            "pictures": extract_gallery_pictures(pictures_sel)
        })
    return metadata


def test_is_male_character(metadata):
    """Test if a character is male."""
    if metadata["description"] and \
            re.search(r"\b(his|he)\b", metadata["description"], flags=re.I):
        return True
    for k, v in metadata["info_fields"]:
        if re.search(r"sex", k, flags=re.I) and \
                re.search(r"\b(male|men|man)\b", v, flags=re.I):
            return True
    return False


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
                        type=argparse.FileType("w"),
                        default=sys.stdout)
    parser.add_argument("--no-parallel",
                        action="store_true",
                        help="""Disable parallel processing.""")
    result = parser.parse_args(argv)
    filenames = [os.path.join(result.pages_directory, name)
                 for name in os.listdir(result.pages_directory)
                 if not name.endswith(".pictures.html")]
    with JSONListStream(result.output) as extract_file:
        for metadata in parmap.map(extract_metadata_from_file,
                                   filenames,
                                   pm_pbar=True,
                                   pm_parallel=not result.no_parallel,
                                   pm_chunksize=10):
            if test_is_male_character(metadata):
                print(f"Skipping {metadata['filename']} as it is a male "
                      f"character.",
                      file=sys.stderr)
                continue
            extract_file.write(metadata)
            result.output.flush()

if __name__ == "__main__":
    main([
        "--pages-directory", r"C:\Users\holli\Documents\Projects\mal-download\pages",
        "--no-parallel",
        "--output", r"C:\Users\holli\Documents\Projects\mal-download\extract.json"
    ])