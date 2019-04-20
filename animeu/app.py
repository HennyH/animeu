# /animeu/app.py
#
# Entrypoint which configures the animeu flask app.
#
# See /LICENCE.md for Copyright information
"""Entrypoint which configures the animeu flask app."""
import os
import json
import random
import urllib.request
import subprocess
import tempfile
from flask import Flask, render_template

# pylint: disable=invalid-name
app = Flask(__name__)

DATA_FILE = os.environ.get("DATA_FILE")
DATA_GOOGLE_DRIVE_ID = os.environ.get("DATA_GOOGLE_DRIVE_ID")
if DATA_FILE:
    with open(DATA_FILE, "rb") as fileobj:
        json_bytes = fileobj.read()
elif DATA_GOOGLE_DRIVE_ID:
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
        json_bytes = fileobj.read()
else:
    raise Exception("Either DATA_FILE or DATA_GOOGLE_DRIVE_ID "
                    "have not been set.")
DATA_JSON = json.loads(json_bytes, encoding="utf8")

@app.route("/")
def index():
    """Render an example page."""
    character1 = random.choice(DATA_JSON)
    character1["pictures"]["gallery"] = \
        [p for p in character1["pictures"]["gallery"] if "23x32" not in p]
    character2 = random.choice(DATA_JSON)
    character2["pictures"]["gallery"] = \
        [p for p in character2["pictures"]["gallery"] if "23x32" not in p]
    return render_template('battle.html', **{
        "left": character1,
        "right": character2
    })
