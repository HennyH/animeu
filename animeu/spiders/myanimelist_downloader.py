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


def make_mal_spider_cls(search_domain):
    """Make a MyAnimeListSpider class."""
    def _none_if_anime_href_not_in_search_domain(href):
        match = re.search(r"/anime/\d+/(?P<name>[^/]+)$", href)
        if match:
            search_name = normalize_text_for_search(match.group("name"))
            if search_name in search_domain["anime"]:
                return href
        return None

    def _none_if_character_href_not_in_search_domain(href):
        match = re.search(r"/character/\d+/(?P<name>[^/]+)$", href)
        if match:
            search_name = normalize_text_for_search(match.group("name"))
            if search_name in search_domain["name"]:
                return href
        return None


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
            Rule(LinkExtractor(allow=r"/anime/\d+/[^/?]+$",
                               process_value=_none_if_anime_href_not_in_search_domain)),
            # go to characters tab
            Rule(LinkExtractor(allow=r"/characters$")),
            # go to each character page
            Rule(
                LinkExtractor(allow=r"/character/\d+/[^/]+$",
                              process_value=_none_if_character_href_not_in_search_domain),
                callback="extract_character"
            )
        )

        # pylint: disable=line-too-long
        def __init__(self, *args, manifest_file=None, pages_directory=None, **kwargs):
            """Initialize a MyAnimeListSpider."""
            super().__init__(*args, **kwargs)
            os.makedirs(pages_directory, exist_ok=True)
            self.manifest_file = manifest_file
            self.pages_directory = pages_directory

        @staticmethod
        def extract_pictures(response):
            """Save the pictures page and update manifest entry."""
            filename = response.meta["filename"]
            response.meta["metadata"]["pictures_stats"] = response.status
            if response.status == 200 and not os.path.exists(filename):
                with open(filename, "wb") as html_fileobj:
                    html_fileobj.write(response.body)

        def extract_character(self, response):
            """Save the character page and update write a manifest entry."""
            character_filename = os.path.join(
                self.pages_directory,
                f"{base64_urlencode(response.url)}.html"
            )
            pictures_filename = os.path.join(
                self.pages_directory,
                f"{base64_urlencode(response.url)}.pictures.html"
            )
            pictures_url = None
            metadata = {}
            if response.status == 200:
                if not os.path.exists(character_filename):
                    with open(character_filename, "wb") as html_fileobj:
                        html_fileobj.write(response.body)
                pictures_tab_sel = response.xpath("//a[text() = 'Pictures']")
                if pictures_tab_sel:
                    pictures_url = pictures_tab_sel.attrib["href"]
                    yield scrapy.Request(pictures_url,
                                         callback=self.extract_pictures,
                                         meta={"filename": pictures_filename,
                                               "metadata": metadata})
            metadata.update({
                "character_status": response.status,
                "character_url": response.url,
                "character_filename": character_filename,
                "pictures_url": pictures_url,
                "pictures_filename": pictures_filename,
            })
            self.manifest_file.write(metadata)

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
    with JSONListStream(result.manifest) as manifest_file:
        spider_cls = make_mal_spider_cls(search_domain)
        process = CrawlerProcess({
            "COOKIES_ENABLED": False,
            "DOWNLOAD_DELAY": 1,
            "RETRY_HTTP_CODES": RETRY_HTTP_CODES + [429]
        })
        process.crawl(spider_cls,
                      manifest_file=manifest_file,
                      pages_directory=result.pages_directory)
        process.start()
        process.join()
