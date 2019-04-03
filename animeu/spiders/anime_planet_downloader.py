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
from scrapy.spiders import CrawlSpider, Rule
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from animeu.spiders.json_helpers import JSONListStream
from animeu.spiders.base64_helpers import base64_urlencode

ANIME_PLANET_URL = "https://www.anime-planet.com"

class AnimePlanetSpider(CrawlSpider):
    """Scraper for anime-planet."""

    name = "animeplanet"
    start_urls = [f"{ANIME_PLANET_URL}/characters/all?gender_id=2&page=1"]

    rules = (
        Rule(
            LinkExtractor(
                deny=r"/all(\?|$)",
                allow=r'/characters/[^/?]+$'
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

    def __init__(self, manifest_file=None, pages_directory=None,
                 *args, **kwargs):
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


def main(argv=None):
    """Entry point to the anime planet link scraper."""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser("""Scrape anime character profiles.""")
    parser.add_argument("--output",
                        metavar="OUTPUT",
                        type=argparse.FileType("w"),
                        default=sys.stdout,
                        required=False)
    parser.add_argument("--pages-directory",
                        metavar="PAGES",
                        type=str,
                        required=True)
    result = parser.parse_args(argv)
    with JSONListStream(result.output) as manifest_file:
        process = CrawlerProcess({
            "COOKIES_ENABLED": False
        })
        process.crawl(AnimePlanetSpider,
                      manifest_file=manifest_file,
                      pages_directory=result.pages_directory)
        process.start()
        process.join()
