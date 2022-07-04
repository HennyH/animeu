# /animeu/common/request_helpers.py
#
# Flask request helper methods.
#
# See /LICENCE.md for Copyright information
"""Flask request helper methods."""
from http import HTTPStatus
from urllib.parse import urlparse, urljoin
from werkzeug.exceptions import HTTPException
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
    if fallback_endpoint:
        return redirect(url_for(fallback_endpoint))
    return redirect("/")

class InvalidQueryParameter(HTTPException):
    """Exception that represents a query parameter being invalid."""

    def __init__(self, description, response=None, code=None, **kwargs):
        """Initialize a new InvalidQueryParameter."""
        super().__init__(**kwargs, description=description, response=response)
        self.code = code or HTTPStatus.BAD_REQUEST

def get_query_parameter(request,
                        name,
                        default=None,
                        expected_cls=str,
                        unpack_single=True):
    """Try get a query parameter(s) from a request."""
    maybe_args = request.args.getlist(name)
    maybe_args = maybe_args or (None if default is None else [default])
    if maybe_args is None:
        return None
    if expected_cls is None \
            or all(isinstance(a, expected_cls) for a in maybe_args):
        parsed_args = maybe_args
    else:
        parsed_args = []
        for arg in maybe_args:
            try:
                parsed_args.append(expected_cls(arg))
            except Exception as error:
                if issubclass(expected_cls, int):
                    # pylint: disable=line-too-long
                    raise InvalidQueryParameter(f"{name} must be a number not: {arg}") from error
                raise InvalidQueryParameter(str(error)) from error
    if unpack_single and len(parsed_args) == 1:
        return parsed_args[0]
    return parsed_args
