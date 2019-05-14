# /animeu/admin/logic.py
#
# Controller logic for the admin module.
#
# See /LICENCE.md for Copyright information
"""Controller logic for the admin module."""
import sys
import threading
import time
from math import ceil
from datetime import datetime
from http import HTTPStatus

from flask import Response
from sqlalchemy.exc import IntegrityError

from animeu.app import db
from animeu.models import Lock
from animeu.api import error_response
from animeu.elo.elo_leaderboard_updater import update_rankings
from animeu.seed_battles import seed_battles

ELO_LOCK_NAME = "elo-update"
SEED_BATTLES_LOCK_NAME = "seed-battles"
LOCK_NAMES = [ELO_LOCK_NAME, SEED_BATTLES_LOCK_NAME]

def try_take_out_lock(name):
    """Try take out a lock."""
    try:
        lock = Lock(name=name, date=datetime.now(), progress=0)
        db.session.add(lock)
        db.session.commit()
        return lock
    except IntegrityError:
        return None

def try_get_existing_lock(name):
    """Try get an existing lock."""
    return Lock.query.get(name)

def update_rankings_with_lock(lock_name):
    """Update rankings using lock and record progress."""
    lock = Lock.query.get(lock_name)
    try:
        def _update_progress(i, total):
            print(f"elo: updating lock with progress {i}/{total}",
                  file=sys.stderr)
            lock.progress = ceil((i / total) * 100)
            db.session.commit()
        update_rankings(progress_callback=_update_progress)
        time.sleep(10)
        # pylint: disable=bare-except
        try:
            db.session.delete(lock)
            db.session.commit()
        except:
            pass
    except:
        db.session.delete(lock)
        db.session.commit()
        raise

def seed_battles_with_lock(lock_name, iterations):
    """Seed the database with battles using a lock."""
    lock = Lock.query.get(lock_name)
    try:
        def _update_progress(i, total):
            print(f"seed: seeding battles with progress {i}/{total}",
                  file=sys.stderr)
            lock.progress = ceil((i / total) * 100)
            db.session.commit()
        seed_battles(iterations, _update_progress)
        time.sleep(10)
        # pylint: disable=bare-except
        try:
            db.session.delete(lock)
            db.session.commit()
        except:
            pass
    except:
        db.session.delete(lock)
        db.session.commit()
        raise


# pylint: disable=too-many-return-statements
def handle_locking_action_request(request, lock_name, action, *args):
    """Handle a request made to a action which locks resource."""
    if lock_name not in LOCK_NAMES:
        return error_response(HTTPStatus.BAD_REQUEST,
                              f"Unkown lock name: {lock_name}")
    maybe_existing_lock = try_get_existing_lock(lock_name)
    if maybe_existing_lock and request.method == "DELETE":
        db.session.delete(maybe_existing_lock)
        db.session.commit()
        return Response(status=HTTPStatus.OK)
    if request.method == "DELETE":
        return Response(status=HTTPStatus.NOT_MODIFIED)
    if maybe_existing_lock and request.method == "GET":
        return Response(str(maybe_existing_lock.progress),
                        status=HTTPStatus.OK)
    if request.method == "GET":
        return Response(status=HTTPStatus.NO_CONTENT)
    if request.method == "POST":
        maybe_lock = try_take_out_lock(lock_name)
        if not maybe_lock:
            return error_response(HTTPStatus.SERVICE_UNAVAILABLE,
                                  f"Failed to take out lock: {lock_name}")
        thread = threading.Thread(target=action, args=(maybe_lock.name, *args))
        thread.start()
        return Response(str(maybe_lock.progress), status=HTTPStatus.CREATED)
    return error_response(HTTPStatus.BAD_REQUEST)
