# /common/func_helpers.py
#
# General purpose functional helper functions.
#
# See /LICENCE.md for Copyright information
"""Functional helper functions."""

from functools import reduce


def compose(*functions):
    """Compose a series of functions left to right.

    f, g, k, ... => x -> f(g(k(...(x))))
    """
    # pylint: disable=undefined-variable
    return reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)


def identity(arg):
    """Return the value."""
    return arg


def constant(value):
    """Return a function which always returns a specific value."""
    # pylint: disable=unused-argument
    def _inner(*args, **kwargs):
        return value
    return _inner


def call(*args, **kwargs):
    """Return a function which invokes its argument."""
    def _inner(func):
        return func(*args, **kwargs)
    return _inner


def starcall(func):
    """Return a function which invokes `func` with destructred args."""
    def _inner(destructable):
        return func(*destructable)
    return _inner

def pipeline(*funcs, arg):
    """Construct a pipeline of composed funcs and invoke it with an arg.

    pipeline(f, g, x) -> f(g(x))
    """
    return compose(*funcs)(arg)


_FALLBACK_NO_DEFAULT = object()

def fallbacks(*funcs, test=None, default=_FALLBACK_NO_DEFAULT):
    """Return a function which invokes functions till a result is returned."""
    if not any(funcs) and default == _FALLBACK_NO_DEFAULT:
        raise ValueError(
            "funcs must not be empty if there is no default value "
            "configued."
        )
    def _inner(*args, **kwargs):
        last_error = None
        for func in funcs:
            try:
                result = func(*args, **kwargs)
            # pylint: disable=bare-except,broad-except
            except Exception as error:
                last_error = error
            else:
                if test is not None and not test(result):
                    continue
                return result
        if default == _FALLBACK_NO_DEFAULT:
            # pylint: disable=raising-bad-type
            raise last_error
        return default
    return _inner
