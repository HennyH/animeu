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
from animeu.models import (User,
                           WaifuPickBattle,
                           FavouritedWaifu,
                           ELORankingCalculation)
from .queries import (get_base_datatables_query,
                      apply_pagination_parameters_to_datatables_query)
from .logic import (ELO_LOCK_NAME,
                    SEED_BATTLES_LOCK_NAME,
                    try_get_existing_lock,
                    handle_locking_action_request,
                    update_rankings_with_lock,
                    seed_battles_with_lock)

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
    maybe_elo_lock = try_get_existing_lock(ELO_LOCK_NAME)
    maybe_elo_calc = ELORankingCalculation.query\
        .order_by(ELORankingCalculation.date.desc())\
        .first()
    maybe_seed_lock = try_get_existing_lock(SEED_BATTLES_LOCK_NAME)
    active_tab = request.args.get("tab", "elo")
    return render_template("admin.html",
                           maybe_elo_lock=maybe_elo_lock,
                           maybe_elo_calc=maybe_elo_calc,
                           maybe_seed_lock=maybe_seed_lock,
                           active_tab=active_tab)

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
@admin_required
def delete_user(user_id):
    """Delete a user."""
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    return Response(status=HTTPStatus.NO_CONTENT)

@admin_bp.route("/battles/<battle_id>", methods=["DELETE"])
@admin_required
def delete_battle(battle_id):
    """Delete a battle."""
    WaifuPickBattle.query.filter_by(id=battle_id).delete()
    db.session.commit()
    return Response(status=HTTPStatus.NO_CONTENT)

@admin_bp.route("/favourited-waifus/<favourited_waifu_id>", methods=["DELETE"])
@admin_required
def delete_favourited_waifu(favourited_waifu_id):
    """Delete a favourited waifu."""
    FavouritedWaifu.query.filter_by(id=favourited_waifu_id).delete()
    db.session.commit()
    return Response(status=HTTPStatus.NO_CONTENT)

@admin_bp.route("/action/elo", methods=["GET", "POST", "DELETE"])
@admin_required
def maybe_update_elo_rankings():
    """Maybe update the ELO rankings if they aren't already updating."""
    return handle_locking_action_request(request,
                                         ELO_LOCK_NAME,
                                         update_rankings_with_lock)

@admin_bp.route("/action/seed", methods=["GET", "POST", "DELETE"])
@admin_required
def maybe_seed_battles():
    """Maybe seed the database with a number of battles."""
    return handle_locking_action_request(request,
                                         SEED_BATTLES_LOCK_NAME,
                                         seed_battles_with_lock,
                                         int(request.form.get("number", 1000)))
