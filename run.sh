#!/bin/bash

pushd /home
    source virtualenv/bin/activate
    flask run --host 0.0.0.0
popd
