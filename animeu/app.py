# /animeu/app.py
#
# Entrypoint which configures the animeu flask app.
#
# See /LICENCE.md for Copyright information
"""Entrypoint which configures the animeu flask app."""
import sys
import os
import json
import random
from flask import Flask, render_template
from flask_webpack import Webpack
from animeu.common.filehelpers import open_transcoded

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
DATA_JSON = json.loads(open(DATA_FILE, "rb").read(), encoding="utf8")

def maybe_first(indexable, default=None):
    try:
        return indexable[0]
    except IndexError:
        return default

# 5678 is the default attach port in the VS Code debug configurations
# print("Waiting for debugger attach")
# ptvsd.enable_attach(address=('localhost', 5678), redirect_output=True)
# ptvsd.wait_for_attach()

@app.route("/")
def index():
    """Render an example page."""
    character = random.choice(DATA_JSON)
    print(character)
    return render_template('battle.html', **{
        "left": {
            "img": maybe_first(character["pictures"]["display"]),
            "name": {
                "en": maybe_first(character["names"]["en"]),
                "jp": maybe_first(character["names"]["jp"])
            },
            "description": maybe_first(character["descriptions"]),
            "tags": character["tags"],
            "info_fields": character["info_fields"]
        }
    })
