# /animeu/api/api.py
#
# Route definitions for the API module.
#
# See /LICENCE.md for Copyright information
"""Route definitions for the authentication module."""
import os
from base64 import b64encode
from http import HTTPStatus
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, url_for, request, g
from werkzeug.http import HTTP_STATUS_CODES

from animeu.app import db, basic_auth, token_auth
from animeu.auth.logic import maybe_find_user
from animeu.models import User
from animeu.common.request_helpers import \
    InvalidQueryParameter, get_query_parameter
from .queries import paginate_query_characters

MAXIMUM_TOKEN_EXPIRY = timedelta(days=30)
DEFAULT_TOKEN_EXPIRY_SECONDS = 3600

# pylint: disable=invalid-name
api_bp = Blueprint("api_bp",
                   __name__,
                   url_prefix="/api",
                   template_folder="templates")

@basic_auth.verify_password
def verify_basic_auth_and_maybe_attach_user_to_context(email, password):
    """Test if the credentials provided via basic auth are valid."""
    maybe_user = maybe_find_user(email, password)
    if not maybe_user:
        return False
    g.current_user = maybe_user
    return True

@token_auth.verify_token
def verify_token_and_maybe_attach_user_to_context(token):
    """Verify a token and if valid attach a user object to the context."""
    maybe_user = User.query.filter_by(api_token=token).first()
    if not maybe_user:
        return False
    if maybe_user.api_token_expiry <= datetime.now():
        return False
    g.current_user = maybe_user
    return True

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

@api_bp.route("token", methods=["GET"])
@basic_auth.login_required
def get_api_token():
    """Provide an API token if the user is an admin."""
    if not g.current_user.is_admin:
        return error_response(HTTPStatus.UNAUTHORIZED,
                              "Only admins can request API keys.")
    expiry_seconds = \
        int(request.args.get("expiry", DEFAULT_TOKEN_EXPIRY_SECONDS))
    expiry_offset = min([
        MAXIMUM_TOKEN_EXPIRY,
        timedelta(seconds=expiry_seconds)
    ])
    g.current_user.api_token_expiry = datetime.now() + expiry_offset
    g.current_user.api_token = b64encode(os.urandom(64)).decode("utf-8")
    db.session.commit()
    return g.current_user.api_token

# pylint: disable=too-many-arguments
@api_bp.route("characters", methods=["GET"])
@token_auth.login_required
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
