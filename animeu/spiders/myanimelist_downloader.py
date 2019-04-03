# /animeu/spiders/myanimelist_downloader.py
#
# Scraper for https://myanimelist.net/character.php to download female characters.
#
# See /LICENCE.md for Copyright information
"""Scraper for myanimelist.net."""
import os
import sys
import argparse
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from animeu.spiders.json_helpers import JSONListStream
from animeu.spiders.base64_helpers import base64_urlencode

MAL_URL = "https://myanimelist.net"

class MyAnimeListSpider(CrawlSpider):
    """Scraper for myanimelist."""

    name = "myanimelist"
    start_urls = [f"{MAL_URL}/character.php"]

    rules = (
        Rule(
            LinkExtractor(allow=r"/character/\d+/",
                          restrict_xpaths="//table"),
            callback="extract_character"
        ),
        Rule(LinkExtractor(allow=r"\?limit=\d+"))
    )

    def __init__(self, manifest_file=None, pages_directory=None,
                *args, **kwargs):
        """Initialize a MyAnimeListSpider."""
        super().__init__(*args, **kwargs)
        os.makedirs(pages_directory, exist_ok=True)
        self.manifest_file = manifest_file
        self.pages_directory = pages_directory


    def extract_pictures(self, response):
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


def main(argv=None):
    """Entry point to the myanimelist link scraper."""
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
        process.crawl(MyAnimeListSpider,
                      manifest_file=manifest_file,
                      pages_directory=result.pages_directory)
        process.start()
        process.join()
