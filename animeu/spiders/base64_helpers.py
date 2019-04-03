# /animeu/spiders/base64_helpers.py
#
# Helpers for dealing with base 64.
#
# See /LICENCE.md for Copyright information
"""Helpers for dealing with base 64."""
from base64 import b64decode, b64encode

def base64_urlencode(text, encoding="utf8"):
    """Return a url safe base64 encoded version of the text."""
    return b64encode(text.encode(encoding), altchars=b"-_").decode("utf8")

def base64_urldecode(b64str, encoding="utf8"):
    """Return the decoded version of url safe encoded base64 string."""
    return b64decode(b64str, altchars=b"-_").decode("utf8")