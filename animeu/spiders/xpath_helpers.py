# /animeu/spiders/common/xpath.py
#
# XPath helper methods to use with ```parsel.Selector```.
#
# See /LICENCE.md for Copyright information
"""XPath helper methods to use with ```parsel.Selector```."""

from functools import partial
from itertools import chain

import regex as re
from lxml import etree
from parsel import Selector, SelectorList

from animeu.common.func_helpers import identity, constant
from animeu.common.iter_helpers import window


def _remove_newlines(text):
    return re.sub(r"\s+", " ", text)


def xpath_count(selector, xpath):
    """Return the number of elements selected by an xpath expression."""
    results = selector.xpath(f"count({xpath})").extract()
    if not results:
        return 0
    count = results[0]
    return int(float(count))


def xpath_position_of(selector, xpath):
    """Return the position of an element relative to its parent."""
    preceding_xpath = f"{xpath}/preceding-sibling::*"
    if not any(selector.xpath(preceding_xpath)):
        return 0
    return xpath_count(selector, preceding_xpath) + 1


def xpath_expr_set_eq(set_a_xpath, set_b_xpath):
    """Return an xpath expression which checks for set equality.

    If two node sets have the same number of nodes, and the number of nodes
    resulting from the union of both node sets is the same as the number of
    nodes in one of those two original node sets, then they must be the same
    sets. If they are not, then the union must contain at least one more node
    than either individual set.
    """
    return (
        rf"("
        rf"  count(({set_a_xpath}) | ({set_b_xpath})) = count({set_a_xpath}) "
        rf"  and count({set_a_xpath}) = count({set_b_xpath}) "
        rf")"
    )


def xpath_expr_first(xpath):
    """Return an xpath expression which selects the first node of a set."""
    return f"({xpath})[1]"


def xpath_boolean(selector, xpath):
    """Return a True/False value for a given xpath expression."""
    results = selector.xpath(xpath)
    # the reason we do > 1 is because an xpath like '1 = 1' will return a
    # '0' or '1' element which we need to evalue further.
    if len(results) > 1:
        return True
    if not any(results):
        return False
    maybe_zero_or_one = results[0].get()
    if maybe_zero_or_one == "1":
        return True
    return False

def xpath_slice_between(selector, lower_xpath, upper_xpath, inclusive=False):
    """Slice a selector between two bounds."""
    if any(not re.match(r"\./(?:\w+|\*)(\[.*?\])?$", xpath)
           for xpath in (lower_xpath, upper_xpath)):
        raise ValueError(
            f"""One or more of {[lower_xpath, upper_xpath]} are a nested or non-relative xpath """
            """expressions which are not supported. All boundary paths must """
            """be of the form ```./e[...]```."""
        )
    max_lower_position = xpath_position_of(
        selector,
        xpath_expr_first(
            # the idea here is that the 'lower' boundary could actually
            # also occur after an 'end' boundary so we can't simply
            # take the last() lower boundary, instead we need to make sure
            # we take the last() out of those who have an 'upper' boundary
            # that follows them.
            # pylint: disable=line-too-long
            f"({lower_xpath})[following-sibling::*[{xpath_expr_is_subset('.', f'../{upper_xpath}')}]]"
        )
    )
    upper_boundary_positions = [
        xpath_position_of(s, '.') for s in  selector.xpath(upper_xpath)
    ]
    upper_boundary_positions = [
        b for b in upper_boundary_positions if b > max_lower_position
    ]
    min_upper_position = \
        upper_boundary_positions[0] if upper_boundary_positions else 0
    # there is simply no way we can select anything out of (?, 0) unless
    # the range is inclusive!
    if min_upper_position == 0 and not inclusive:
        return SelectorList()
    lwr_op = ">=" if inclusive else ">"
    upr_op = "<=" if inclusive else "<"
    slice_expr = (
        r"*[ "
        f"  position() {lwr_op} {max_lower_position} "
        f"  and position() {upr_op} {min_upper_position} "
        rf"]"
    )
    return selector.xpath(slice_expr)


def xpath_expr_is_subset(set_a_xpath, set_b_xpath):
    """Return an xpath expression which checks if `a` is a subset of `b`."""
    # pylint: disable=line-too-long
    return rf"(count(({set_a_xpath}) | ({set_b_xpath})) = count({set_b_xpath}))"


def etree_parse_single_element(element_html):
    """Parse the html of a single element as into an ```etree.Element```."""
    try:
        html_body_wrapped_element = etree.HTML(element_html)
    except ValueError as error:
        print(f"Error: could not parse the html:\n {element_html}")
        raise error
    elements = list(html_body_wrapped_element.xpath("/html/body/*"))
    assert len(elements) == 1
    return elements[0]


def istag(selector, tags):
    """Return True if the selector is for an element which matches any tags."""
    if isinstance(tags, str):
        tags = (tags,)
    tags = tuple(t.lower().strip() for t in tags)
    element_tag = selector.xpath("local-name(.)").get().lower().strip()
    return element_tag in tags


# pylint: disable=too-many-arguments
def xpath_split(selector,
                boundary_xpaths,
                child_filter=None,
                map_group=identity,
                filter_results=None,
                include_boundaries=True):
    """Split a selector list up by boundary xpaths."""
    if not isinstance(selector, (SelectorList, list)):
        raise TypeError("Expected `selector` to be a SelectorList or a list.")
    splits = [[]]
    for sel in selector:
        if any(any(sel.xpath(q)) for q in boundary_xpaths):
            if include_boundaries:
                splits.append([sel])
            else:
                splits.append([])
        else:
            splits[-1].append(sel)
    splits = map(partial(filter, child_filter), splits)
    splits = filter(bool, splits)
    splits = map(SelectorList, splits)
    splits = map(SelectorList, map(map_group, splits))
    splits = map(SelectorList, filter(filter_results, splits))
    return SelectorList(list(splits))


# pylint: disable=too-many-locals
def xpath_split_inner(selector,
                      boundary_xpaths,
                      child_filter=None,
                      map_group=None,
                      filter_results=None):
    """Split a selectors children up and re-wrap segments in parent.

    ```
    <div> h2' p p h2" p p <div>
    becomes
    [<div> h2' p p </div>, <div> h2" p p </div>]
    ```
    """
    if any(not re.match(r"\./(?:\w+|\*)(\[.*?\])?$", xpath)
           for xpath in boundary_xpaths):
        raise ValueError(
            f"""One or more of {boundary_xpaths} are a nested or non-relative xpath """
            """expressions which are not supported. All boundary paths must """
            """be of the form ```./e[...]```."""
        )

    if isinstance(selector, SelectorList):
        if len(selector) != 1:
            raise ValueError(
                """The provided `selector` was a SelectorList with """
                """either zero or more than one elements. This is not """
                """supported, provide either a Selector or SelectorList """
                """with a single element."""
            )
        selector = selector[0]
    outer_html = selector.extract()

    def map_elements_to_selector(element_htmls):
        """Wrap elements in a copy of the parent element."""
        root = etree_parse_single_element(outer_html)
        for child in list(root):
            root.remove(child)
        for element_html in element_htmls:
            element = etree_parse_single_element(element_html)
            root.append(element)
        root_html = etree.tostring(root, encoding="utf8").decode("utf8")
        root_html = _remove_newlines(root_html)
        return Selector(text=root_html).xpath("/html/body/*[1]")

    def wrap_if_bare_text(html, wrapper_tag="p"):
        """Wrap bare text up in a tag."""
        if not re.match(r"^\<[^>]+\>", html):
            return "<{tag}>{html}</{tag}>".format(tag=wrapper_tag,
                                                  html=html)
        return html

    number_of_splits = sum(
        map(partial(xpath_count, selector), boundary_xpaths)
    )
    if number_of_splits == 0:
        return [SelectorList([selector])]

    # In this section we collect all the unique boundary positions.
    # so say for ```h2' p p h2" p p p'``` splitting on ``./h2``` we would get
    # [1, 4] initally. However we want a list of the form [a, b, c] such that
    # we have spans [a, b), [b, c) which in total comprise all elements.
    # To ensure that we end up with such a form
    # we ensure that the left-most element is added as boundary unless
    # it already is (h2' in this example), we also ensure the right-most
    # element is added as a boundary unless it already is - which in this
    # example would be p' which was not included so we add a position to
    # include it. Resulting in [1, 4, 8] which corresponds to the spans
    # [1, 4) = [h2', p, p], [4, 8) = [h2", p, p, p'].
    #
    # Another example of ```h2' p h2"``` we would get inital boundaries of
    # [1, 3] which would be padded to [1, 3, 4] resulting in ranges
    # [1, 3) = [h2', p] and [3, 4) = [h2"]
    # pylint: disable=invalid-name
    unordered_split_boundary_positions = set()
    maximum_position = xpath_count(
        selector,
        "./*"
    )
    for boundary_xpath in boundary_xpaths:
        number_of_boundaries = xpath_count(selector, boundary_xpath)
        for boundary_number in range(1, number_of_boundaries + 1):
            boundary_element_xpath = f"({boundary_xpath})[{boundary_number}]"
            position_relative_to_parent = xpath_position_of(
                selector,
                boundary_element_xpath
            )
            unordered_split_boundary_positions.add(
                position_relative_to_parent
            )
    # pylint: disable=invalid-name
    ordered_split_boundary_positions = list(
        sorted(unordered_split_boundary_positions)
    )
    if ordered_split_boundary_positions[0] > 1:
        ordered_split_boundary_positions.insert(0, 1)
    if ordered_split_boundary_positions[-1] <= maximum_position:
        ordered_split_boundary_positions.append(maximum_position + 1)

    results = []
    for inclusive_start_pos, noninclusive_end_pos in window(
            ordered_split_boundary_positions
    ):
        slice_xpath = (
            # The second expression here involving ```string-length``` is to
            # account for leftover text that isn't wrapped in any element.
            # for example:
            # ```
            # <div>
            #   <h2>h1</h2>
            #   foo
            #   <h2>h2</h2>
            #   ...
            # </div>
            # ```
            # In this scenario the 'foo' text is accessed via /text() not /*.
            # We grab out these bare text nodes by 'intersecting' 1) all the
            # text nodes that occur before the end element and 2) all the text
            # elements that occur after the start element:
            # <------------------------e
            #     s------------------------>
            #     |--------------------|
            # y y | x t   x  t t   x t | y y
            (
                f"./*[position() >= {inclusive_start_pos} and position() < {noninclusive_end_pos}] | "  # pylint: disable=line-too-long
                f"set:intersection("
                f"   ./*[position() = {noninclusive_end_pos}]/preceding-sibling::text()[string-length(normalize-space()) > 1], "  # pylint: disable=line-too-long
                f"   ./*[position() = {inclusive_start_pos}]/following-sibling::text()[string-length(normalize-space()) > 1]"  # pylint: disable=line-too-long
                f")"   # pylint: disable=line-too-long
            ).format(start_pos=inclusive_start_pos,
                     end_pos=noninclusive_end_pos)
        )
        # Filter out cruft elements that are not of interested. For example
        # unused paragraph tags, so as to achieve a more unified structure
        # in the results.
        elements_in_slice = selector.xpath(slice_xpath)
        filtered_elements = SelectorList(
            filter(child_filter, elements_in_slice)
        )
        mapped_elements = map_group(filtered_elements) if map_group else \
            filtered_elements
        if not isinstance(mapped_elements, SelectorList):
            raise TypeError("""Expected the supplied `map_group` function """
                            """to return a ```parsel.SelectorList``` not """
                            f"""a {type(mapped_elements)}.""")
        element_htmls = list(
            chain.from_iterable(e.getall() for e in mapped_elements)
        )
        if not element_htmls:
            continue
        element_htmls = map(_remove_newlines, element_htmls)
        element_htmls = map(wrap_if_bare_text, element_htmls)
        results.append(map_elements_to_selector(element_htmls))
    return SelectorList(filter(filter_results, results))


def normalize_whitespace(text, translate_nbsp=True, only_single_spaces=True):
    """Normalize whitespace and change ```&nbsp;``` to a normal space."""
    if translate_nbsp:
        text = text.replace("\xa0", " ")
    text = text.replace("\u2019", "'")
    text = text.replace("\u00c2", " ")
    if only_single_spaces:
        if translate_nbsp:
            text = re.sub(r"[^\S\n]+", " ", text)
        else:
            text = re.sub(r"[^\S\n\xa0]+", " ", text)
    text = text.strip()
    return text


def get_all_text(sel,
                 element_seperator="\n",
                 element_filter=constant(True),
                 element_transform=identity,
                 text_transform=normalize_whitespace) -> str:
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
    return text_transform(text)
