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
from flask_webpack import Webpack

# pylint: disable=invalid-name
app = Flask(__name__)
app.config.update({
    "WEBPACK_MANIFEST_PATH": os.path.join(os.path.dirname(__file__),
                                          "..",
                                          "build",
                                          "manifest.json"),
    "WEBPACK_ASSETS_URL": "http://localhost:9000/"
})

# pylint: disable=invalid-name
webpack = Webpack()
webpack.init_app(app)

DATA_FILE = os.environ.get("DATA_FILE")
with open(DATA_FILE, "r") as data_fileobj:
    DATA_JSON = json.load(data_fileobj)

@app.route("/")
def index():
    """Render an example page."""
    character = random.choice(DATA_JSON)
    return render_template('smash-or-pass.html', **{
        "left": {
            "img": character["picture"],
            "name": character["name"],
            "description": "A micro framework",
            "tags": character["tags"],
            "info": {
                "Hair Color:": character["hair_color"],
                "Age:": "18",
                "Birthdate:": "24th June",
                "Height": "180cm"
            }
        }
    })
