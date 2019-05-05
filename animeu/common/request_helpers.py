# /animeu/common/request_helpers.py
#
# Flask request helper methods.
#
# See /LICENCE.md for Copyright information
"""Flask request helper methods."""
from urllib.parse import urlparse, urljoin
from flask import redirect, url_for

def is_safe_url(request, target):
    """Test if a given target URL is a safe redirect target.

    Taken from: http://flask.pocoo.org/snippets/62/
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

def arg_redirect(request,
                 arg_name="next",
                 fallback_url=None,
                 fallback_endpoint=None):
    """Maybe redirect to a provided URL argument or a fallback location."""
    url = request.args.get(arg_name)
    if url and is_safe_url(request, url):
        return redirect(url)
    if fallback_url:
        return redirect(fallback_url)
    elif fallback_endpoint:
        return redirect(url_for(fallback_endpoint))
    else:
        return redirect("/")
