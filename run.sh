#!/bin/bash

source /home/virtualenv/bin/activate
flask run --host 0.0.0.0 --port "${PORT:-5000}"
