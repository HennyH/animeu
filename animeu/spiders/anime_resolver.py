# /animeu/spiders/anime_resolver.py
#
# Module for resolving a known anime from an anime name.
#
# See /LICENCE.md for Copyright information
"""Module for resolving a known anime from an anime name."""

from animeu.spiders.xpath_helpers import \
    xpath_split_inner, xpath_slice_between, get_all_text

def extract_anime_metadata_from_myanimelist_page(sel):
    """Extract the anime metadata from a myanimelist page."""
    main_title = get_all_text(sel.xpath("//h1/span[@itemprop='name']"))
    info_bar_sel = sel.xpath("//div[@class='js-scrollfix-bottom']")
    alternative_titles_section_sel = xpath_slice_between(
        info_bar_sel,
        lower_xpath="./h2[. = 'Alternative Titles']",
        upper_xpath="./br"
    )
    alternative_title_sels = xpath_split_inner(
        alternative_titles_section_sel,
        boundary_xpaths=["./div"]
    )


