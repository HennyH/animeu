# animeu/spiders/xpath_helpers.py
#
# Helpers to assist with extraction.
#
# See /LICENCE.md for Copyright information
"""Helpers to assist with extraction."""
import re
from parsel import Selector, SelectorList

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
