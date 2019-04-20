# /animeu/app.py
#
# Entrypoint which configures the animeu flask app.
#
# See /LICENCE.md for Copyright information
"""Entrypoint which configures the animeu flask app."""
import os
import json
import random
from flask import Flask, render_template

# pylint: disable=invalid-name
app = Flask(__name__)

DATA_FILE = os.environ.get("DATA_FILE")
DATA_JSON = json.loads(open(DATA_FILE, "rb").read(), encoding="utf8")

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
