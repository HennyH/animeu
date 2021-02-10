# animeu [![Build Status](https://travis-ci.com/HennyH/animeu.svg?token=zsZqz8ak9yekVpEX2Qnc&branch=master)](https://travis-ci.com/HennyH/animeu)
Battle of the anime babes!

# Setup

## Development

To set up a development environment fro the project you're encouraged to create a virtual environment and activate it during development. Regardless you will perform the following steps:

```bash
pip install -r requirements.dev.<linux | windows>.txt
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

## How do I favourite a waifu?

You may have noticed on the profile page there is a 'Waifus for Laifu' list, this is a list of the waifus you have favourited. If you're wondering how to favourite a waifu simply click the love-heart shaped button near their name in either battle mode, or on their info card which is accessible by clicking a link with their name. To unfavourite them (meanie!) just press the button again.

![how to favourite](./docs/favourite-button.PNG)

# Development

There is quite a lot of ground to cover in terms of how the project was developed because a lot of additional work was done around acquiring character data for _most_ (we did our due dilligence by blacklisting ceartin tags!) anime characters, and in around configuring both CI with Travis and CD with Heroku. I'll give a quick overview of the different areas in semi-chronological order:

## Data Collection

An anime babe battle site wouldn't be very useful if there are no babes to battle! To solve this problem I decided to scrape both [Anime Planet](https://www.anime-planet.com/) and [My Anime List](https://myanimelist.net/). Part of the issue was MAL did not allow you to filter characters to only girls but had the better collection of pictures/metadata. This meant that we either had to download _every single_ character page on MAL just to then work out which ones to throw away because they were male. That would be extreemly inefficent especially because MAL lists extreemly minor (extras basically) characters. The solution to this problem was as follows:

1. Scrape AP which allows for filtering by gender.
2. Extract the metadata from the AP page(s).
3. Feed the AP extract into the MAL downloader to only visit known (anime, character) pairs.
4. Extact the metadata from the MAL page(s).
5. Fuzzy-match & combine the AP and MAL extracts to form a single `characters.json`

One particular design decision to note is that the extract format was 'normalized', so that an extract from either page could be used with the database however it would just be of lesser quality. This also made the 'merge' step nice and generic and composable `many extracts -> extract`.

All the scraping and extraction code are exposed via CLI programs as defined in `setup.py` - feel free to give them a try yourself.

## Travis CI

Everyone loves linting - and test are good also. I set up Travis CI so that we could lint all of our python to very strict standards and run our test code at every commit and before every merge. This allowed us to maintain a high quality of code throughout the project, and not leaving it all to the last minute!

The travis set up wasn't too complicated - except that some trickery was required to get a newer version of sqlite3 and compatible versions of chromium and chromium-webdriver installed. We use Xvfb as a virtual framebuffer in order to run our selenium based integration tests.

## Heroku Deployments

We used Heroku's docker support to easily build and deploy the site on every commit to master. We used a docker file so that we could test the builds locally without resorting to annoying buildpacks. On heroku we had to use a Postgres SQL database because the storage is ephemeral and would be wiped away on each container restart - someone could lose their newly discovered waifus! unacceptable!

## The 'App'  Itself

### Structure

We organised the project in a component-as-a-folder structure, where each component was some high level section of the site such as the feed, profile, elo rankings, admin tools, etc... This approach worked well with Flask's blueprints system and allowed for us to keep our template code (html, css, js) nearer to the python code responsible for handling that page.

```
/animeu
    /testing
    /spiders
    /api
    /battle
        /templates
        battle.py
        logic.py
        queries.py
    ...
    app.py
    models.py
```

Within each component we placed heavily database related code into a `queries.py` file and the controller code in `logic.py`. Care was taken the avoid the use of unnessacery OOP, instead I wrote the python code in a more functional style - allowing for mor easy code re-use between pages. I think it is also conceptually simpler, more composable and in principle easier to test.

### All The Macros!

We made heavy use of macros and the `call` templating method in our templates. This allowed us to have massive amounts of code reuse - for example the battle page's template was simply:

```jinja
{% block body %}
    {% macro battle_card(id, character, form) %}
        {% set en_name = character["names"]["en"][0] %}
        {% call(is_header, is_body, is_footer) character_card(id, character) %}
            {% if is_footer %}
                <div class="card-footer">
                    <button type="button" class="btn btn-outline-secondary jump-to-top">
                        <i class="fas fa-arrow-up"></i>
                    </button>
                    <form method="POST" action="{{ url_for('battle_bp.submit_battle') }}">
                        {{ form.csrf_token(id=id+"csrf") }}
                        {{ form.winner_name(id=id+"winner", required=False) }}
                        {{ form.loser_name(id=id+"loser", required=False) }}
                        <button class="btn btn-outline-primary proposal-button">
                            Make <b class="proposal-name">{{ en_name.split() | first }}</b> your waifu!
                        </button>
                    </form>
                </div>
            {% endif %}
        {% endcall %}
    {% endmacro %}
    <section class="battle-grid">
        {{ battle_card("left", left, left_form) }}
        {{ battle_card("right", right, right_form) }}
    </section>
{% endblock body %}
```

You may be thinking why are there `is_header`, `is_body` type varaibles being passed into the caller? Well the answer is because we wanted multi-slot transclusion to override or enhance specific parts of a templated macro. This technique allowed us to significantly improve the extensibility of our macros and improve code re-use.

### Bootstrap Grid System? No Thanks!

You may have noticed that the site has a very responsive design - it doesn't just wrap content around when a fixed breakpoint is reached (the bootstrap approach), no, no, we go much further than that! We will _change_ the design of components based on viewport constraints! For an example of this just take a look at the feed's battle card summaries and how they transition:

#### On a desktop with the window expanded...

![battles-large-mode](./docs/feed-responsive-large.PNG)

#### To on the same desktop with the window shrunk (but before the cards warp!)

![battles-small-mode](./docs/feed-responsive-small.PNG)

This allows users to view the two lists side-by-side on a wider range of displays (seeing the picture/name/win/loss is the main information) before laying out the cards one atop the other. To achieve this the whole site was built of CSS Grid. The use of CSS grid was also critical to our template and CSS re-use as we often wanted the same elements to be displayed but in different positions, and/or with additional content added (e.g more counters in the win/loss v.s the ELO leaderboard). We could then override the grid properties to display the content as needed. Awesome!

## Integration Testing

In order to get bonus marks for writing integration tests, but also satisfy the requirement (and it would be good practice anyway) to have code coverage statistics I had to do a bit of work to run browser based tests but record coverage of all the python code that ran on the backend. The most important pieces of code to achieve this is the use of `coverage.process_startup()` in both `app.py` and `test_server.py`, and the polling of the server in `ServerThread.wait_till_server_ready()` which prevented the automated tests from starting until the server was _actually_ ready to process requests. There was also an annoying issue about cached module imports and how these are shared between threads which essentially resulted in the `db` (imported from `app.py`) to keep using the value of `DATABASE` it was initially imported with even after the environment variable was reset (and seeminly even `importlib.reload` didn't help!). The workaround was to use a single temporary file as the database and just `rm` it after each test fixture. The end result is we can test both our frontend code and the backend at the same time! Woohoo!

```
The command "FLASK_APP=animeu.app python -Wignore -m unittest animeu.testing.integration_tests" exited with 0.
$ coverage combine
The command "coverage combine" exited with 0.
$ coverage report
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
animeu/about/__init__.py                    2      0   100%
animeu/about/about.py                       5      1    80%
animeu/admin/__init__.py                    2      0   100%
animeu/admin/admin.py                      71      9    87%
animeu/admin/logic.py                      85     22    74%
animeu/admin/queries.py                    70     12    83%
animeu/api/__init__.py                      2      0   100%
animeu/api/api.py                          67      7    90%
animeu/api/queries.py                      39      6    85%
animeu/app.py                              61      3    95%
animeu/auth/__init__.py                     2      0   100%
animeu/auth/auth.py                        35      0   100%
animeu/auth/forms.py                       15      0   100%
animeu/auth/logic.py                       14      1    93%
animeu/battle/__init__.py                   2      0   100%
animeu/battle/battle.py                    30      0   100%
animeu/battle/forms.py                      6      0   100%
animeu/common/request_helpers.py           40      8    80%
animeu/data_loader.py                      35      3    91%
animeu/elo/elo_algorithim.py               23      0   100%
animeu/elo/elo_leaderboard_updater.py      45      8    82%
animeu/feed/__init__.py                     2      0   100%
animeu/feed/feed.py                        10      0   100%
animeu/feed/logic.py                       32      2    94%
animeu/feed/queries.py                     24      2    92%
animeu/info/__init__.py                     2      0   100%
animeu/info/info.py                        20      1    95%
animeu/info/queries.py                     15      2    87%
animeu/models.py                           40      0   100%
animeu/profile/__init__.py                  2      0   100%
animeu/profile/logic.py                    28      2    93%
animeu/profile/profile.py                  25      2    92%
animeu/profile/queries.py                  15      1    93%
animeu/seed_battles.py                     72     10    86%
-----------------------------------------------------------
TOTAL                                     938    102    89%
The command "coverage report" exited with 0.
```

# The Bonus Marks

In this section I'll enumerate the work done outside the original scope which I beleive can merit bonus marks:

1. Setting up CI with Travis so it ran linters and integration tests in headless mode.
2. Setting up CD with Heroku and Postgres SQL using a Dockerfile (see the site https://animeu.herokuapp.com/battle/ and http://www.animeu.io (WIP))
3. Writing comprehensive integration tests while also capturing python code coverage.
4. The use of mostly custom CSS (grid/flexbox) to layout all the elements rather than using boostraps simple grid system and the development of a custom carousel (the TINY buttons and lag of bootstraps one annoyed me).
5. Scraping MAL and AP to produce a complete dataset for a production ready site.
6. REST API with token auth for searching character metadata (w/ paginator)

# Super Explicit Instructions For Markers

One issue with trying to set up a virtual environment with all the dependencies required to run the scrapers, extractors, tests and app you will need ceartin build tools and development headers. On OSX that requires installing the Xcode Command Line Tools and using homebrew to install a new version of python, on windows you need the Visual Studio Command Line Tools and on linux you'll need python development headers, etc... This is messy and everyone has one issue or another setting all that up. That said you can try the following before falling back to using docker:

## To run ONLY the app and integration tests:

```bash
python -m virtualenv env
source env/bin/activate
pip install -r requirements.txt
pip install -e .
export FLASK_APP="animeu.app"
export FLASK_ENV="development"
# the syntax for this url is explained here https://docs.sqlalchemy.org/en/13/core/engines.html#sqlite you should use the app.db bundled in the submission OR use a new one but populate the database using the admin tools - use the seed battles functionality AND THEN GENERATE TEH ELO RANKINGS! THIS IS NOT AUTOMATED!!
export DATABASE="sqlite:///<absolute-path-to-database | /relative-path-to-database>"
# this is a path to the JSON file you download from google drive (look in the Setup section for the link, it should also be in the submission zip).
export DATA_FILE="characters.json"
flask run

# The app will now be running... if you want to run the tests just shut it down (or leave it running it works either way)
mkdir drivers
cd drivers
# adjust for your version of chrome and OS
curl https://chromedriver.storage.googleapis.com/74.0.3729.6/chromedriver_mac64.zip > chromedriver.zip
unzip chromedriver.zip
chmod +x chromedriver
cd ..
export PATH="$PATH:./drivers"
NO_HEADLESS=1 python -Wignore -m unittest animeu.testing.integration_tests
# wait for the tests to finish then run
coverage combine
coverage report
# you should now see the coverage results
```

## To run EXTRACTOR/DOWNLOADERS:

These scripts have additional dependencies which you can install by following the steps to run the app only and then the following command:

```bash
pip install -r requirements.dev.linux.txt # or .dev.windows.txt if you're on windows
```

You can now invoke the CLI programs as detailed in `setup.py`:

```py
setup(...,
      entry_points={
        "console_scripts": [
            "anime-planet-downloader=animeu.spiders.anime_planet_downloader:main",
            ...
        ]
      ])
```

just like any other program like so:

```bash
$ anime-planet-downloader -h
usage: Scrape anime character profiles. [-h] [--manifest OUTPUT]
                                        --pages-directory PAGES

optional arguments:
  -h, --help            show this help message and exit
  --manifest OUTPUT
  --pages-directory PAGES
```

## Running everything if you can't install the dependencies

As a last resort we can use docker to run the app - this is what's used in production so if production is working and you have master it should almost ceartinly work! It doesn't automatically set the `DATA_FILE` for you but we can instead use the `DATA_GOOGLE_DRIVE_ID` to point it to a file on google drive (used to avoid needing to set up S3 and keeping character data in the repository). This should let you run the app in the most simple way.

```bash
docker build -t animeu .
docker run -p 5000:5000 \
           -e DATA_GOOGLE_DRIVE_ID="1ua7-Jb2RVaTDgjmuQZneGMz102GjthVc" \
           -e DATABASE_URL="sqlite:////home/app.db" \
           -it animeu
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 48155c59684d, empty message
INFO  [alembic.runtime.migration] Running upgrade 48155c59684d -> 8b86a6fbc0a6, empty message
INFO  [alembic.runtime.migration] Running upgrade 8b86a6fbc0a6 -> b400e1a221ed, empty message
INFO  [alembic.runtime.migration] Running upgrade b400e1a221ed -> 4746d5353df9, empty message
INFO  [alembic.runtime.migration] Running upgrade 4746d5353df9 -> 2893736abf82, empty message
INFO  [alembic.runtime.migration] Running upgrade 2893736abf82 -> f416a60b44df, empty message
/home/virtualenv/lib/python3.6/site-packages/alembic/util/messaging.py:73: UserWarning: Skipping unsupported ALTER for creation of implicit constraint
  warnings.warn(msg)
INFO  [alembic.runtime.migration] Running upgrade f416a60b44df -> dbd25bb3e82b, empty message
INFO  [alembic.runtime.migration] Running upgrade dbd25bb3e82b -> bfadd4ebe86d, empty message
INFO  [alembic.runtime.migration] Running upgrade bfadd4ebe86d -> de7e464a7b7f, empty message
INFO  [alembic.runtime.migration] Running upgrade de7e464a7b7f -> 4a29fc6a553c, empty message
 * Serving Flask app "animeu.app"
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
172.17.0.1 - - [19/May/2019 12:29:08] "GET /battle/ HTTP/1.1" 302 -
172.17.0.1 - - [19/May/2019 12:29:08] "GET /login?next=%2Fbattle%2F HTTP/1.1" 200 -
```

You can now at least run the app! If you wanted to run the extractors/downloaders you could in theory you could simply edit the dockerfile to install the development dependencies and then `docker run -it animeu /bin/sh` and run the commands from inside the container...

Running the tests I'm not sure about, you may be able to install chromium and chromium-webdriver using the package manager and run Xvfb like on the CI server but I don't know if that will work. If worst comes to worse just look at the travis log in the submission to see the tests passing and the coverage and then look at the code in `integration_tests.py`, the `self.subTest(...)` are pretty short and self explanatory.

## A suggested test script:

1. Go to the register page and sign up and try the following a) enter short/long usernames and passwords, b) use the recaptcha to prove you're human, c) try register again using the same email.
2. If you're already signed in from step 1 sign out and then use the sign in page to sign back in using the admin account `henry@gmail.com` and `password123`.
3. Go to the admin tools and do the following a) use the 'Battles' tab to seed some extra battles in the database, b) try delete a battle, c) go to the users and favourited waifu tabs and use the search boxes and column sorting options, d) use the ELO tab to upate the rankings based on your new battles.
4. Go to the battle page and have some fun doing a couple of battles - use the info and gallery images to toggle different modes on the card.
5. Try favourite / unfavourite a character by clicking the love heart button on the battle page.
6. Go to you profile and check that your favourited waifus and recent battles match up.
7. Go to the feed and try the different leaderboard types.
8. Start re-sizing the browser, perhaps turning on dev tools and choosing devices like iPhone X, iPad Pro, etc... to test the responsiveness of the site.
9. Click on a charcters name to view their info page.
10. Go the the about page to learn more.

# References

|Name | Type | Description | Useage |
|-----|------|-------------|--------|
pylint|tool|Advanced linter for python|Used to lint the python code
pydocstyle|tool|Linter for comments in python|Used to ensure the codedocs are well written
scrapy|library|A scraping framework|Used to scrape MAL/AP
parmap|library|Parallel processing library to easily scale out workloads|Used to parallelize the extraction code
fuzzywuzzy[speedup]|library|Fuzzy matching library for python|Used to help match up MAL characters with AP characters
cchardet|library|Detects file encodings|Used to help transcode downloaded files in the extractors
youtube-dl|tool|Helps download things from various sites|Used to download files from google drive
regex|library|Alternative regex library for python|Used to allow for timeouts in character API which uses regexes
tqdm|library|Simple progress bars|Used in the extractor to show task progress
coverage|tool|Reports python test coverage|Used with in the tests to detect line coverage and display results
cheroot|library|WSGI server|Used to start up the app in a safe way for our tests
selenium|libray|Browser automation tool|Used to drive the automation tests
requests|library|Web request simplifier|Used to test the character search API
Flask|||
Flask-SQLAlchemy|||
Flask-Migrate|||
Flask-Login|||
Flask-WTF|||
Flask-HTTPAuth|||
MAL Characters|dataset|MAL's collection of character data|Providing characters to battle with
AP Characters|dataset|AP's collection of character data|Providing characters to battle with
