# /animeu/app.py
#
# Entrypoint which configures the animeu flask app.
#
# See /LICENCE.md for Copyright information
"""Entrypoint which configures the animeu flask app."""

import os
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

@app.route("/")
def index():
    """Render an example page."""
    return render_template('base.html')
