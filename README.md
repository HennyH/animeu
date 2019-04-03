# animeu [![Build Status](https://travis-ci.com/HennyH/animeu.svg?token=zsZqz8ak9yekVpEX2Qnc&branch=master)](https://travis-ci.com/HennyH/animeu)
Battle of the anime babes

# Setup

Ensure you have python 3.6 installed and create a virtual environment via:

```
python -m virtualenv env
```

Activate the virtualenv enviroment using `./env/Scripts/activate` and then run `python setup.py develop`.

# Running

In one terminal start webpack-dev-server by running `npm run watch`. In another terminal ensure you activate your python virtalenv and then set the `FLASK_ENV` to `development` then run `flask run`.

```
> ./env/Scripts/activate
(env) > $env:FLASK_ENV="development"
(env) > flask run
 * Environment: development
 * Debug mode: on
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 108-231-407
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```
