# /animeu/spiders/myanimelist_downloader.py
#
# Scraper for https://myanimelist.net/character.php to download female characters.
#
# See /LICENCE.md for Copyright information
"""Scraper for myanimelist.net."""
import os
import sys
import argparse
import re
import json
from string import punctuation
from functools import lru_cache

import parsel
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from scrapy.settings.default_settings import RETRY_HTTP_CODES

from animeu.spiders.json_helpers import JSONListStream
from animeu.spiders.base64_helpers import base64_urlencode

try:
    # pylint: disable=unused-import
    import ijson.backends.yajl2_cffi as ijson
except ImportError:
    sys.stderr.write("""Falling back to slower pure-python ijson\n""")
    # pylint: disable=unused-import
    import ijson

MAL_URL = "https://myanimelist.net"


def normalize_text_for_search(text):
    """Normalize text for case/punctutation/whitespace insensitive search."""
    text = text.translate(str.maketrans("", "", punctuation))
    text = text.lower()
    text = re.sub(r"\s", "", text)
    return text


def make_mal_spider_cls(manifest_file, pages_directory, search_domain, already_downloaded):
    """Make a MyAnimeListSpider class."""
    os.makedirs(pages_directory, exist_ok=True)

    def _none_if_character_href_not_in_search_domain(href):
        match = re.search(r"/character/\d+/(?P<name>[^/]+)$", href)
        if match:
            search_name = normalize_text_for_search(match.group("name"))
            character_url = f"{MAL_URL}{match.group()}"
            character_filename = f"{base64_urlencode(character_url)}.html"
            if search_name not in search_domain["name"]:
                return None
            if character_filename not in already_downloaded:
                return href
            gallery_url = \
                get_gallery_url_from_character_file(character_filename)
            gallery_filename = f"{base64_urlencode(character_url)}.pictures.html"
            if gallery_url and gallery_filename not in already_downloaded:
                return href
            manifest_file.write({
                "character_status": 200,
                "character_url": character_url,
                "character_filename": character_filename,
                "pictures_url": gallery_url,
                "pictures_filename": gallery_filename,
            })
            print(
                f"Already downloaded character={href}, pictures={gallery_url}",
                file=sys.stderr
            )
        return None

    @lru_cache(maxsize=None)
    def get_gallery_url_from_character_file(filename):
        """Extract the gallery url from a character file."""
        with open(os.path.join(pages_directory, filename), "r", encoding="utf-8") as file_obj:
            sel = parsel.Selector(text=file_obj.read())
        anchor = sel.xpath("//a[text() = 'Pictures']")
        if anchor is None:
            return None
        return anchor.attrib["href"]

    class MyAnimeListSpider(CrawlSpider):
        """Scraper for myanimelist."""

        name = "myanimelist"
        start_urls = [
            # pylint: disable=line-too-long
            f"{MAL_URL}/anime.php?q=&type=1&score=0&status=0&p=0&r=0&sm=1&sd=1&sy=1980&em=0&ed=0&ey=0&c[0]=a&c[1]=b&c[2]=c&c[3]=f&gx=0&o=3&w=1&show=0",
        ]

        rules = (
            # pagiante the table
            Rule(
                LinkExtractor(allow=r"show=\d+",
                              restrict_xpaths="(//a[contains(., 'Next')])[1]")
            ),
            # visit animes in table
            Rule(LinkExtractor(allow=r"/anime/\d+/[^/?]+$"),
                 callback="extract_anime"),
            # go to characters tab
            Rule(LinkExtractor(allow=r"/characters$")),
            # go to each character page
            Rule(
                LinkExtractor(allow=r"/character/\d+/[^/]+$",
                              process_value=_none_if_character_href_not_in_search_domain),
                callback="extract_character"
            )
        )

        @staticmethod
        def extract_pictures(response):
            """Save the pictures page and update manifest entry."""
            pictures_filename = response.meta["filename"]
            if response.status == 200 and not os.path.exists(pictures_filename):
                with open(os.path.join(pages_directory, pictures_filename), "wb") as html_fileobj:
                    html_fileobj.write(response.body)
            response.meta["metadata"].update({
                "pictures_status": response.status,
                "pictures_url": response.url,
                "pictures_filename": pictures_filename
            })

        @staticmethod
        def extract_character(response):
            """Save the character page and write a manifest entry."""
            character_filename = f"{base64_urlencode(response.url)}.html"
            character_filepath = \
                os.path.join(pages_directory, character_filename)
            if response.status == 200:
                if not os.path.exists(character_filepath):
                    with open(character_filepath, "wb") as html_fileobj:
                        html_fileobj.write(response.body)
                pictures_url = \
                    get_gallery_url_from_character_file(character_filename)
                pictures_filename = \
                    f"{base64_urlencode(response.url)}.pictures.html"
                if pictures_filename in already_downloaded:
                    print(f"Skipping already downloaded character "
                          f"picutes: {pictures_url} -> {pictures_filename}",
                          file=sys.stderr)
                else:
                    yield scrapy.Request(
                        pictures_url,
                        callback=MyAnimeListSpider.extract_pictures,
                        meta={"filename": pictures_filename,
                              "metadata": response.meta["metadata"]}
                    )
            response.meta["metadata"].update({
                "character_status": response.status,
                "character_url": response.url,
                "character_filename": character_filename
            })

        @staticmethod
        def extract_characters(response):
            """Extract all the characters on the page."""
            character_anchors = response.xpath(
                "//div[@id = 'content']//a[contains(@href, '/character/') and not(contains(@class, 'fw-n'))]"
            )
            character_metadatas = []
            for anchor in character_anchors:
                character_url = anchor.attrib["href"]
                if _none_if_character_href_not_in_search_domain(character_url):
                    character_metadata = {}
                    character_metadatas.append(character_metadata)
                    yield scrapy.Request(
                        character_url,
                        callback=MyAnimeListSpider.extract_character,
                        meta={"metadata": character_metadata}
                    )
            response.meta["metadata"].update({
                "characters": character_metadatas
            })

        def extract_anime(self, response):
            """Save the anime page write a manifest entry."""
            anime_filename = f"{base64_urlencode(response.url)}.anime.html"
            anime_filepath = os.path.join(pages_directory, anime_filename)
            metadata = {
                "anime_url": response.url,
                "anime_filename": anime_filename
            }
            if response.status == 200:
                if not os.path.exists(anime_filepath):
                    with open(anime_filepath, "wb") as html_fileobj:
                        html_fileobj.write(response.body)
                characters_tab_url = response\
                    .xpath("//div[@id='horiznav_nav']//a[contains(., 'Characters')]")\
                    .attrib["href"]
                yield scrapy.Request(
                    characters_tab_url,
                    callback=MyAnimeListSpider.extract_characters,
                    meta={"metadata": metadata}
                )
            manifest_file.write(metadata)

    return MyAnimeListSpider

def load_search_domain(anime_planet_extract):
    """Load the search domain (characters & animes) from the AP extract."""
    def iter_items():
        with open(anime_planet_extract, "r") as extract_fileobj:
            extract = json.load(extract_fileobj)
        for character in extract:
            if not any(ar["role"] in ("Main", "Secondary")
                       for ar in character["anime_roles"]):
                continue
            for anime in character["anime_roles"]:
                yield ("anime", anime["name"])
            for en_name in character["names"]["en"]:
                yield ("name", en_name)
    domain = {"anime": set(), "name": set()}
    for item_type, item_value in iter_items():
        domain[item_type].add(normalize_text_for_search(item_value))
    return domain

def main(argv=None):
    """Entry point to the myanimelist link scraper."""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser("""Scrape anime character profiles.""")
    parser.add_argument("--anime-planet-extract",
                        metavar="EXTRACT",
                        type=str,
                        required=True)
    parser.add_argument("--manifest",
                        metavar="MANIFEST",
                        type=argparse.FileType("w"),
                        default=sys.stdout,
                        required=False)
    parser.add_argument("--pages-directory",
                        metavar="PAGES",
                        type=str,
                        required=True)
    result = parser.parse_args(argv)
    search_domain = load_search_domain(result.anime_planet_extract)
    already_downloaded = os.listdir(result.pages_directory)
    with JSONListStream(result.manifest) as manifest_file:
        spider_cls = make_mal_spider_cls(manifest_file,
                                         result.pages_directory,
                                         search_domain,
                                         already_downloaded)
        process = CrawlerProcess({
            "COOKIES_ENABLED": False,
            "DOWNLOAD_DELAY": 1,
            "RETRY_HTTP_CODES": RETRY_HTTP_CODES + [429]
        })
        process.crawl(spider_cls)
        process.start()
        process.join()
