# /animeu/api/api.py
#
# Route definitions for the API module.
#
# See /LICENCE.md for Copyright information
"""Route definitions for the authentication module."""
from http import HTTPStatus
from flask import Blueprint, jsonify, url_for, request
from werkzeug.http import HTTP_STATUS_CODES
from animeu.common.request_helpers import \
    InvalidQueryParameter, get_query_parameter
from .queries import paginate_query_characters

# pylint: disable=invalid-name
api_bp = Blueprint("api_bp",
                   __name__,
                   url_prefix="/api",
                   template_folder="templates")

def error_response(status_code, message=None):
    """Construct an API error response."""
    response = jsonify({
        "error": HTTP_STATUS_CODES.get(status_code, "Unkown Error"),
        "message": message
    })
    response.status_code = status_code
    return response

@api_bp.errorhandler(InvalidQueryParameter)
def handle_invalid_query_parameter(error):
    """Handle an InvalidQueryParamter exception being raised."""
    if error.response:
        return error.response
    return error_response(error.code, message=error.description)

# pylint: disable=too-many-arguments
@api_bp.route("characters", methods=["GET"])
def paginate_characters(page=0, limit=100, anime=None, name=None,
                        tags=None, description=None):
    """Return a subset of the character information as a JSON response."""
    page = get_query_parameter(request, "page", page, int)
    limit = get_query_parameter(request, "limit", limit, int)
    anime = get_query_parameter(request, "anime", anime)
    name = get_query_parameter(request, "name", name)
    tags = get_query_parameter(request, "tag", tags, unpack_single=False)
    description = get_query_parameter(request, "description", description)
    if page < 0:
        return error_response(HTTPStatus.BAD_REQUEST,
                              "Page must be non-negative")
    if limit <= 0:
        return error_response(HTTPStatus.BAD_REQUEST,
                              "Limit must be greater than zero")
    filter_kwargs = {"anime": anime, "name": name, "tags": tags,
                     "description": description}
    result = paginate_query_characters(page=page, limit=limit, **filter_kwargs)
    maybe_previous_page = None if page == 0 else \
        url_for("api_bp.paginate_characters", page=page - 1, limit=limit,
                **filter_kwargs)
    maybe_next_page = None if (page + 1) * limit >= result["total"] \
        else url_for("api_bp.paginate_characters", page=page + 1, limit=limit,
                     **filter_kwargs)
    result["previous_page"] = maybe_previous_page
    result["next_page"] = maybe_next_page
    return jsonify(result)
