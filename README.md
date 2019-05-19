# animeu [![Build Status](https://travis-ci.com/HennyH/animeu.svg?token=zsZqz8ak9yekVpEX2Qnc&branch=master)](https://travis-ci.com/HennyH/animeu)
Battle of the anime babes!

# Setup

## Development

To set up a development environment fro the project you're encouraged to create a virtual environment and activate it during development. Regardless you will perform the following steps:

```bash
pip install -r requirements.<linux | windows>.dev.txt
pip install -e .
export FLASK_APP="animeu.app"
export FLASK_ENV="development"
export DATABASE="sqlite:///$(pwd)/app.db" # specify the SQLAlchemy compatible database URI to use as the apps db
export NO_HEADLESS=1 # show the browser window when running tests
```

You will also need a `character.json` file which contains all the characters - you can either re-create this file using the downloaders and extractors or use the one [here](https://drive.google.com/file/d/1ua7-Jb2RVaTDgjmuQZneGMz102GjthVc/view?usp=sharing). When you've downloaded the file ensure export a `DATA_FILE` env var with its location:

```bash
export DATA_FILE=characters.json
```

Now simply run the app:

```bash
(env) PS C:\Users\holli\Documents\Projects\animeu> flask run
 * Serving Flask app "animeu.app" (lazy loading)
 * Environment: development
 * Debug mode: on
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 208-161-861
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
USING DATABASE = sqlite:///C:/Users/holli/Documents/Projects/animeu/app.db
```

## Tests

To run the integration tests you will need a recent version of chrome and a suitable chromdriver binary in your `PATH`. If you have stable chrome then simply grab the latest chromdriver and place in a `drivers` folder and then run the tests like so:

```bash
coverage erase # remove any coverage files previously generated
PATH="$PATH:./drivers" python -Wignore -m unittest animeu.testings.integration_tests
coverage combine # merge the coverage results of all our subprocesses
coverage report # view the coverge results from the terminal
    ...
coverage html # generate a useful HTML report
python -m http.server # create a HTTP server exposing the current directroy
```

You can then navigate to `http://localhost:8000/htmlcov/index.html` (note that the port number may be different for your HTTP server...) to view the coverage results.

## Docker

A Dockerfile has been included which allows you to easily build an image which runs the site just as it is run in production. An example usage of this Dockerfile is:

```bash
docker build -t animeu .
docker run -p 5000:5000 \
           -e DATA_FILE=/home/data/characters.json \
           -e DATABASE="sqlite:////home/data/app.db" \
           -v "$HOME/animeu-data:/home/data" \
           -it animeu
```

The most important points to note here is exposing the default `5000` port and mounting a volume which contains a `characters.json` and then setting our `DATA_FILE` env var just like in development.

# Design

## What is Animeu?

Animeu is designed to be a fun site for showing love for anime characters and to find new anime. The characters of a show can sometimes be just as important as the plot in determining how enjoyable an anime might be. By allowing users to 'battle' characters off against each other and generate leaderboards a list of the most enjoyable characters will emerge. In addition the site was designed to display a lot of visual information to allow users to quickly see a lot of characters - untill they have love at first sight!

## What are these 'battles'?

A battle is the voting method in the app, from these battles various rankings are calculated. Each battle is simply the presentation of two anime characters, the user is then asked to choose which character they want to be their waifu. This choice results in both a winner (the waifu) and loser (the rejected character).

After one battle another is immedietly shown - allowing the user to quickly discover new characters. An important factor here is that characters are chosen for the battles randomly, this prevents characters becoming highly rated just because they are more _well known_!

![battle screen](./docs/battle.PNG)

## How do I see the top waifus?

You can view the rankings which are calulated from all the battles on the feed page. On the feed there are two sections:

1. *Leaderboard:* The leadboard offers a dropdown to select a type of ranking to use, and then displays the top characters according to that ranking.
2. *Recent Battles:* These are simply all the recent battles conducted by _any_ user - not just you!

The available ranking types are avaliable from the leaderboard dropdown:

1. *Highest ELO:* These are the characters with the greatest ELO rankings. ELO is a type of ranking algorithim used in competitive games such as Chess, League of Legends, DOTA, etc...
2. *Lowest ELO:* The expact opposite of _Highest ELO_, this shows the worst performing waifus according to their ELO ranks.
3. *Top Waifus:* These are the waifus with the most wins, regardless of how many losses they've had.
4. *Active Waifus:* These are the waifus who have seen the most battles.

![feed screen](./docs/feed.PNG)

## I want to know more about a cuite waifu I saw! Help me!

Don't worry, we understand how a waifu displayed in the feed may capture your heart at first sight. If you want to know more just click on their name and you'll be taken to their info page.

![link to profile](./docs/link-to-profile.PNG)


## How do I favourite a waifu?

You may have noticed on the profile page there is a 'Waifus for Laifu' list, this is a list of the waifus you have favourited. If you're wondering how to favourite a waifu simply click the love-heart shaped button near their name in either battle mode, or on their info card which is accessible by clicking a link with their name.

![how to favourite](./docs/favourite-button.PNG)

# Development

How was it all developed...