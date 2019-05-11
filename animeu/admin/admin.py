# /animeu/admin/admin.py
#
# Route definitions for the admin module.
#
# See /LICENCE.md for Copyright information
"""Route definitions for the admin module."""
import json
from http import HTTPStatus
from flask import Blueprint, render_template, request, jsonify, Response
from flask_login import login_required, current_user

from animeu.app import db
from animeu.models import User, WaifuPickBattle, FavouritedWaifu
from .queries import \
    get_base_datatables_query, apply_pagination_parameters_to_datatables_query

# pylint: disable=invalid-name
admin_bp = Blueprint("admin_bp",
                     __name__,
                     url_prefix="/admin",
                     template_folder="templates")

def admin_required(func):
    """Require the current user to be an administrator."""
    def _inner(*args, **kwargs):
        if current_user.is_admin:
            return func(*args, **kwargs)
        return Response(HTTPStatus.UNAUTHORIZED)
    return login_required(func)

@admin_bp.route("/", methods=["GET"])
@admin_required
def admin_page():
    """Render the admin page."""
    return render_template("admin.html")

@admin_bp.route("/dt/users", methods=["POST"])
@admin_required
def users_datatable():
    """Respond to the user datatables ajax calls."""
    parameters = json.loads(request.get_data())
    base_query = get_base_datatables_query(User,
                                           parameters,
                                           ignore_columns=["password_hash"])
    records_total = User.query.count()
    records_filtered = db.engine.scalar(base_query.count())
    data_query = \
        apply_pagination_parameters_to_datatables_query(base_query, parameters)
    data = list(map(dict, db.engine.execute(data_query).fetchall()))
    return jsonify({
        "draw": str(int(parameters["draw"])),
        "recordsTotal": records_total,
        "recordsFiltered": records_filtered,
        "data": data
    })

@admin_bp.route("/dt/battles", methods=["POST"])
@admin_required
def battles_datatable():
    """Respond to the battle datatables ajax calls."""
    parameters = json.loads(request.get_data())
    base_query = get_base_datatables_query(WaifuPickBattle, parameters)
    records_total = WaifuPickBattle.query.count()
    records_filtered = db.engine.scalar(base_query.count())
    data_query = \
        apply_pagination_parameters_to_datatables_query(base_query, parameters)
    data = list(map(dict, db.engine.execute(data_query).fetchall()))
    return jsonify({
        "draw": str(int(parameters["draw"])),
        "recordsTotal": records_total,
        "recordsFiltered": records_filtered,
        "data": data
    })

@admin_bp.route("/dt/favourites", methods=["POST"])
@login_required
@admin_required
def favourited_waifus():
    """Respond to the favourited waifu datatables ajax calls."""
    parameters = json.loads(request.get_data())
    base_query = get_base_datatables_query(FavouritedWaifu, parameters)
    records_total = FavouritedWaifu.query.count()
    records_filtered = db.engine.scalar(base_query.count())
    data_query = \
        apply_pagination_parameters_to_datatables_query(base_query, parameters)
    data = list(map(dict, db.engine.execute(data_query).fetchall()))
    return jsonify({
        "draw": str(int(parameters["draw"])),
        "recordsTotal": records_total,
        "recordsFiltered": records_filtered,
        "data": data
    })

@admin_bp.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    """Delete a user."""
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    return Response(status=HTTPStatus.NO_CONTENT)

@admin_bp.route("/battles/<battle_id>", methods=["DELETE"])
def delete_battle(battle_id):
    """Delete a battle."""
    WaifuPickBattle.query.filter_by(id=battle_id).delete()
    db.session.commit()
    return Response(status=HTTPStatus.NO_CONTENT)

@admin_bp.route("/favourited-waifus/<favourited_waifu_id>", methods=["DELETE"])
def delete_favourited_waifu(favourited_waifu_id):
    """Delete a favourited waifu."""
    FavouritedWaifu.query.filter_by(id=favourited_waifu_id).delete()
    db.session.commit()
    return Response(status=HTTPStatus.NO_CONTENT)
