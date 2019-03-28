import os
from flask import Flask, url_for, render_template
from flask_webpack import Webpack

app = Flask(__name__)
app.config.update({
    "WEBPACK_MANIFEST_PATH": os.path.join(os.path.dirname(__file__),
                                          "build",
                                          "manifest.json"),
    "WEBPACK_ASSETS_URL": "http://localhost:9000/"
})

webpack = Webpack()
webpack.init_app(app)

@app.route("/")
def index():
    return render_template('base.html')
