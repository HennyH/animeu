# /animeu/spiders/myanime_anime_extractor.py
#
# Extract the metadata of animes from anime myanimelist pages.
#
# See /LICENCE.md for Copyright information
"""Extract the metadata of animes from anime myanimelist pages."""
import sys
import os
import re
import argparse
from fnmatch import filter as fnfilter
from typing import Iterable
from functools import partial

from tqdm import tqdm
from collections import namedtuple
from parsel import Selector

from animeu.common.iter_helpers import lookahead
from animeu.common.file_helpers import JSONListStream
from animeu.spiders.xpath_helpers import \
    xpath_slice_between, get_all_text, normalize_whitespace

AnimeName = namedtuple("AnimeName", ["name", "is_primary"])
KeyValuesPair = namedtuple("KeyValuesPair", ["key", "values"])

def select_sidebar(sel: Selector) -> Selector:
    """Select the info sidebar."""
    return sel.xpath("//div[@class='js-scrollfix-bottom']")

def extract_anime_names(sel: Selector) -> Iterable[AnimeName]:
    """Extract the names of the anime."""
    main_title_text = get_all_text(sel.xpath("//h1/span[@itemprop='name']"))
    yield AnimeName(name=main_title_text, is_primary=True)
    alternative_titles_sel = xpath_slice_between(
        select_sidebar(sel),
        lower_xpath="./h2[. = 'Alternative Titles']",
        upper_xpath="./br"
    )
    for alternative_title_sel in alternative_titles_sel:
        maybe_many_names = get_all_text(
            alternative_title_sel.xpath("./span/following-sibling::text()")
        )
        for name in re.split(r"\b\s*,\s+(?=[A-Z][a-z])", maybe_many_names):
            yield AnimeName(name=name, is_primary=False)

def extract_anime_description(sel: Selector) -> str:
    """Extract the anime description."""
    description_paragraph_sels = \
        sel.xpath("//span[@itemprop='description']/text()")
    paragraphs = []
    for paragraph_sel, is_last in lookahead(description_paragraph_sels):
        content = get_all_text(paragraph_sel)
        # pylint: disable=invalid-name
        IS_PROBABLY_SOURCE_MAX_LEN = 30
        # pylint: disable=line-too-long
        if is_last and \
                re.search(r"written|from|source|author", content, flags=re.I) and \
                len(content) <= IS_PROBABLY_SOURCE_MAX_LEN:
            continue
        paragraphs.append(content)
    return normalize_whitespace("\n".join(paragraphs))

def extract_anime_info_fields(sel: Selector) -> Iterable[KeyValuesPair]:
    """Extract info fields of the anime."""
    stat_sels = xpath_slice_between(
        select_sidebar(sel),
        lower_xpath="./h2[. = 'Information']",
        upper_xpath="./br"
    )
    for stat_sel in stat_sels:
        key = re.sub(r"\s+", " ", get_all_text(stat_sel.xpath("./span")))\
            .strip()\
            .rstrip(":")
        # pylint: disable=line-too-long
        value_text = \
            re.sub(r"\s+", " ", get_all_text(stat_sel).replace(key, "", 1)).strip()
        values = re.split(r"\b\s+,\s+\b", value_text)
        yield KeyValuesPair(key=key, values=values)

def extract_anime_picture_url(sel: Selector) -> str:
    """Extract the URL of the anime's main picture."""
    return select_sidebar(sel).xpath("//img[@class='ac']").attrib.get("src")

def extract_anime_metadata(sel: Selector) -> dict:
    """Extract all the metadata of an anime into a dict."""
    names = extract_anime_names(sel)
    description = extract_anime_description(sel)
    info_fields = extract_anime_info_fields(sel)
    picture_url = extract_anime_picture_url(sel)
    return {
        "names": [{"name": n.name, "is_primary": n.is_primary} for n in names],
        "description": description,
        "info_fields":
            [{"name": f.key, "values": f.values} for f in info_fields],
        "picture": picture_url
    }

def main(argv: list = None):
    """Entry point to the MAL anime metadata extractor."""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser("""MAL Anime Extractor""")
    parser.add_argument("--directory", type=str, required=True)
    parser.add_argument("--filter", type=str, default="*.anime.html")
    parser.add_argument("--output",
                        type=argparse.FileType("w", encoding="utf8"),
                        default=sys.stdout)
    result = parser.parse_args(argv)
    anime_html_filenames = [
        os.path.join(result.directory, name)
        for name in fnfilter(os.listdir(result.directory), result.filter)
    ]
    with JSONListStream(result.output) as json_stream:
        for anime_filename in tqdm(anime_html_filenames):
            with open(anime_filename, "r", encoding="utf8") as anime_fileobj:
                sel = Selector(text=anime_fileobj.read())
            json_stream.write(extract_anime_metadata(sel))

if __name__ == "__main__":
    main()
