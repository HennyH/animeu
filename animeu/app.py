# /animeu/app.py
#
# Entrypoint which configures the animeu flask app.
#
# See /LICENCE.md for Copyright information
"""Entrypoint which configures the animeu flask app."""
import os
import json
import subprocess
import tempfile
from flask import Flask

DATA_FILE = os.environ.get("DATA_FILE")
DATA_GOOGLE_DRIVE_ID = os.environ.get("DATA_GOOGLE_DRIVE_ID")
if DATA_FILE:
    with open(DATA_FILE, "rb") as fileobj:
        # pylint: disable=invalid-name
        json_bytes = fileobj.read()
elif DATA_GOOGLE_DRIVE_ID:
    # pylint: disable=invalid-name
    data_filename = os.path.join(tempfile.gettempdir(), "characters.json")
    subprocess.run(
        [
            "youtube-dl",
            f"https://drive.google.com/open?id={DATA_GOOGLE_DRIVE_ID}",
            "--output",
            data_filename
        ],
        check=True
    )
    with open(data_filename, "rb") as fileobj:
        # pylint: disable=invalid-name
        json_bytes = fileobj.read()
else:
    raise Exception("Either DATA_FILE or DATA_GOOGLE_DRIVE_ID "
                    "have not been set.")
DATA_JSON = json.loads(json_bytes, encoding="utf8")

# pylint: disable=invalid-name
app = Flask(__name__)

# pylint: disable=wrong-import-position
from animeu.battle import battle_bp
# pylint: disable=wrong-import-position
from animeu.auth import auth_bp

app.register_blueprint(battle_bp)
app.register_blueprint(auth_bp)
