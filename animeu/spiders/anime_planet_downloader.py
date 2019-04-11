# /animeu/spiders/anime_planet.py
#
# Scraper for https://www.anime-planet.com to download female characters.
#
# See /LICENCE.md for Copyright information
"""Scraper for anime-planet.com."""
import os
import sys
import argparse
import scrapy
import json
import itertools
from functools import partial
from operator import itemgetter
from scrapy.spiders import CrawlSpider, Rule
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from animeu.common.funchelpers import compose
from animeu.spiders.json_helpers import JSONListStream
from animeu.spiders.base64_helpers import base64_urlencode, base64_urldecode

try:
    import ijson.backends.yajl2_cffi as ijson
except ImportError:
    sys.stderr.write("""Falling back to slower pure-python ijson\n""")
    import ijson

ANIME_PLANET_URL = "https://www.anime-planet.com"

def make_anime_planet_spider_cls(previously_scraped_urls):
    """Construct an AnimePlanetSpider class."""
    def _none_if_href_already_scraped(href):
        if href in previously_scraped_urls:
            return None
        return href

    class AnimePlanetSpider(CrawlSpider):
        """Scraper for anime-planet."""

        name = "animeplanet"
        start_urls = [f"{ANIME_PLANET_URL}/characters/all?gender_id=2&page=1"]

        rules = (
            Rule(
                LinkExtractor(
                    deny=r"/all(\?|$)",
                    allow=r'/characters/(?!(tags|top-loved|top-hated)$)[^/?]+$',
                    process_value=_none_if_href_already_scraped
                ),
                callback="extract_character"
            ),
            Rule(
                LinkExtractor(
                    allow=r"gender_id=2&page=\d+",
                    restrict_xpaths="//ul[@class='nav']/li[@class='selected']/following-sibling::li[1]"
                ),
                follow=True
            ),
        )

        def __init__(self, manifest_file=None, pages_directory=None, *args,
                     **kwargs):
            """Initialize a AnimePlanetSpider."""
            super().__init__(*args, **kwargs)
            os.makedirs(pages_directory, exist_ok=True)
            self.manifest_file = manifest_file
            self.pages_directory = pages_directory

        def extract_character(self, response):
            """Save the character page to a file and write metadata entry."""
            filename = os.path.join(self.pages_directory,
                                    f"{base64_urlencode(response.url)}.html")
            self.manifest_file.write({
                "url": response.url,
                "status": response.status,
                "name": filename
            })
            if response.status == 200 and not os.path.exists(filename):
                with open(filename, "wb") as html_fileobj:
                    html_fileobj.write(response.body)

    return AnimePlanetSpider

def load_scraped_urls(manifest_filename):
    """Maybe load the scraped urls from a manifest file."""
    if not os.path.exists(manifest_filename):
        return set()
    with open(manifest_filename, "rb") as fileobj:
        return set(item["url"] for item in ijson.items(fileobj, "item"))


def main(argv=None):
    """Entry point to the anime planet link scraper."""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser("""Scrape anime character profiles.""")
    parser.add_argument("--manifest",
                        metavar="OUTPUT",
                        type=str,
                        default=None,
                        required=False)
    parser.add_argument("--pages-directory",
                        metavar="PAGES",
                        type=str,
                        required=True)
    result = parser.parse_args(argv)

    # maybe get the previous manifest entries (to write back out into the new
    # manifest).
    if result.manifest and os.path.exists(result.manifest):
        with open(result.manifest, "r") as fileobj:
            previous_manifest = json.load(fileobj)
    else:
        previous_manifest = []

    with open(result.manifest or sys.stdout, "w") as manifest_fileobj, \
             JSONListStream(manifest_fileobj) as json_stream:
        previously_scraped_urls = set()
        for item in previous_manifest:
            json_stream.write(item)
            previously_scraped_urls.add(item["url"])
        for entry in os.scandir(result.pages_directory):
            filename = os.path.basename(entry.path)
            b64_url, ext = filename.split(".")
            if ext != "html":
                continue
            previously_scraped_urls.add(base64_urldecode(b64_url))
        spider_cls = \
            make_anime_planet_spider_cls(previously_scraped_urls)
        process = CrawlerProcess({
            "COOKIES_ENABLED": False
        })
        process.crawl(spider_cls,
                      manifest_file=json_stream,
                      pages_directory=result.pages_directory,
                      previously_scraped_urls=previously_scraped_urls)
        process.start()
        process.join()
