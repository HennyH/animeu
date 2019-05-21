# /animeu/common/iter_helpers.py
#
# Helper iterator functions built on itertools.
#
# See /LICENCE.md for Copyright information
"""Helper iterator functions built on itertools."""
from collections import Hashable
from functools import partial
from itertools import islice
from typing import Iterable, Tuple, Generic, TypeVar
from types import GeneratorType

T = TypeVar("T")

def chunk(iterable, chunk_size):
    """Make an iterator that returns 'chunk_size'-ed chunks of 'iterable'."""
    # The purpose of this is to support both __iter__ and __getitem__ things.
    iterable_wrapper = iter(iterable)
    # This works by taking `chunk_size` slices out of the iterable,
    # this form of iter() keeps calling the function until the sentinel
    # value is reached, which in this case is the empty tuple. Hence
    # we keep slicing iterable until there are no values left.
    return iter(lambda: tuple(islice(iterable_wrapper, chunk_size)), ())


def lookahead(iterable: Iterable[T]) -> Iterable[Tuple[T, bool]]:
    """Iterate over iterable yielding the value and if it is the last value."""
    iterable_wrapper = iter(iterable)

    # At least return a single value, even if it is None
    try:
        result = next(iterable_wrapper)
    except StopIteration:
        return

    for value in iterable_wrapper:
        yield result, False
        result = value
    yield result, True


def lookaround(iterable):
    """Iterate over iterable yielding the value and if it is a border value."""
    iterable_wrapper = iter(iterable)

    # At least return a single value, even if it is None
    try:
        result = next(iterable_wrapper)
    except StopIteration:
        return

    first = True
    last = False

    for value in iterable_wrapper:
        yield result, first, last
        first = False
        result = value

    last = True
    yield result, first, last


def window(seq, n=2):  # pylint: disable=invalid-name
    """Return a sliding window over data from the iterable.

    Example:
    ```s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...```
    See: https://docs.python.org/release/2.3.5/lib/itertools-example.html
    """
    iterable_wrapper = iter(seq)
    result = tuple(islice(iterable_wrapper, n))
    if len(result) == n:
        yield result
    elif result:
        missing_count = n - len(result)
        yield tuple(result) + tuple([None] * missing_count)
    for elem in iterable_wrapper:
        result = result[1:] + (elem,)
        yield result


def deep_get(indexable, indexes, default=None):
    """Repeatedly index into an object.

    Continues to index into 'indexable' using the indexes in 'indexes',
    until a final value is reached, or an error occurs in which case
    the 'default' or None is returned.
    """
    curr = indexable
    for index in indexes:
        if curr is None:
            return default
        try:
            curr = curr[index]
        except (KeyError, IndexError):
            return default
    return curr


def deep_set(indexable, indexes, value):
    """Set a value at a nested index."""
    def _collection_for_index(index):
        return [None] * index if isinstance(index, int) else {}

    def _value_at_index_is_collection(collection, index):
        try:
            value_at_index = collection[index]
            return isinstance(value_at_index, (dict, list))
        except (KeyError, IndexError):
            return False

    def _padd_list(collection, to_length):
        collection.extend([None] * (to_length - len(collection)))

    def _collection_supports_index(collection, index):
        if isinstance(collection, list) and isinstance(index, int):
            return True
        if isinstance(collection, dict) and isinstance(index, Hashable):
            return True
        return False

    curr = indexable
    for (now_index, next_index), is_last in lookahead(window(indexes, n=2)):
        if isinstance(curr, list):
            _padd_list(curr, now_index + 1)

        if not _collection_supports_index(curr, now_index):
            raise ValueError(
                """Unsupported index {} for collection {}""".format(
                    now_index,
                    curr
                )
            )

        if next_index is not None:
            if not _value_at_index_is_collection(curr, now_index):
                curr[now_index] = _collection_for_index(next_index)
            curr = curr[now_index]
            if isinstance(curr, list):
                _padd_list(curr, next_index + 1)

        if is_last:
            if next_index is None:
                curr[now_index] = value
            else:
                curr[next_index] = value

    return indexable


def pluralise(value, collection_types=(GeneratorType, list)):
    """If value is singular return a collection containing it."""
    if isinstance(value, collection_types):
        return value
    if value is not None:
        return [value]

    return []


def hasattrs(obj, names):
    """Return whether the object has an attribute with the given name(s)."""
    _hasattr = partial(hasattr, obj)
    if isinstance(names, str):
        return _hasattr(names)
    return all(map(_hasattr, names))
