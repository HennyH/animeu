# /animeu/testings/integration_tests.py
#
# Integration tests for the animeu site.
#
# See /LICENCE.md for Copyright information
# pylint: disable=import-outside-toplevel
"""Integration tests for the animeu site."""
import os
import unittest
import re
import random
import json
from http import HTTPStatus
from datetime import datetime
from tempfile import mkstemp

import requests
from sqlalchemy.sql import select, func
from selenium import webdriver
from selenium.common.exceptions import \
    NoSuchElementException, TimeoutException as SeleniumTimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as expect

from animeu.testing.test_server import ServerThread

def get_chrome_options(headless=True):
    """Get a default set of options to launch headless chrome."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("headless")
    options.add_argument("window-size=1920x1080")
    options.add_argument("start-maximized")
    return options

# pylint: disable=too-many-arguments
def wait_for_visible(browser,
                     css_selector=None,
                     id_selector=None,
                     xpath_selector=None,
                     invert=False,
                     timeout=5):
    """Wait for an element to become visible."""
    wait = WebDriverWait(browser, timeout)
    if css_selector:
        locator = (By.CSS_SELECTOR, css_selector)
    elif id_selector:
        locator = (By.ID, id_selector)
    elif xpath_selector:
        locator = (By.XPATH, xpath_selector)
    else:
        raise ValueError("""Must provide a selector.""")
    if invert:
        return wait.until_not(expect.visibility_of_element_located(locator))
    return wait.until(expect.visibility_of_element_located(locator))


def try_fill_out_and_submit_login_form(browser, email, password):
    """Assume we're on the login page and try sign in."""
    email_input = wait_for_visible(browser, "input[name='email']")
    password_input = \
        browser.find_element_by_css_selector("input[name='password']")
    email_input.send_keys(email)
    password_input.send_keys(password)
    submit_button = \
        browser.find_element_by_xpath("//input[@name='submit']")
    submit_button.click()

def perform_login_expecting_success(browser, email, password):
    """Perform a login waiting to be redirected after success."""
    try_fill_out_and_submit_login_form(browser, email, password)
    wait_for_visible(browser, "input[name='email']", invert=True)

class AnimeuIntegrationTestCase(unittest.TestCase):
    """Base class for animeu integration tests."""

    tmp_fd, tmp_filename = mkstemp(prefix="animeu-test-db", suffix=".db")
    os.close(tmp_fd)
    __TEST_DATABASE_FILENAME = tmp_filename

    def __init__(self, *args, **kwargs):
        """Initialize a new animeu test case."""
        super().__init__(*args, **kwargs)

    @classmethod
    # pylint: disable=arguments-differ
    def setUpClass(cls, with_browser=True):
        """Set up a test environment."""
        if os.path.exists(AnimeuIntegrationTestCase.__TEST_DATABASE_FILENAME):
            os.unlink(AnimeuIntegrationTestCase.__TEST_DATABASE_FILENAME)
        os.environ["COVERAGE_PROCESS_START"] = ".coveragerc"
        os.environ["DATABASE"] = os.environ.get(
            "TEST_DATABASE_URL",
            f"sqlite:///{AnimeuIntegrationTestCase.__TEST_DATABASE_FILENAME}"
        )
        headless = "NO_HEADLESS" not in os.environ
        if with_browser:
            cls.browser = \
                webdriver.Chrome(options=get_chrome_options(headless=headless))
            cls.wait = WebDriverWait(cls.browser, 2)
        cls.server_thread = ServerThread()
        cls.server_thread.start()
        cls.server_thread.wait_till_server_ready()
        cls.url_for = cls.server_thread.url_for

    @classmethod
    def tearDownClass(cls):
        """Tear down the environment."""
        cls.server_thread.shutdown()
        cls.server_thread.join()
        if hasattr(cls, "browser"):
            cls.browser.quit()
        if os.path.exists(AnimeuIntegrationTestCase.__TEST_DATABASE_FILENAME):
            os.unlink(AnimeuIntegrationTestCase.__TEST_DATABASE_FILENAME)


class AuthenticationTests(AnimeuIntegrationTestCase):
    """Test the signup and login/logout functionality."""

    TEST_EMAIL = "test@gmail.com"
    TEST_USERNAME = "iamuser"
    TEST_PASSWORD = "password123"
    TEST_PASSWORD_TOO_SHORT = "pw"

    def get_invalid_feedback(self):
        """Get a string of any invalid feedback on the page."""
        invalid_feedback_els = \
            self.browser.find_elements_by_class_name("invalid-feedback")
        return "\n".join([e.text for e in invalid_feedback_els])

    def get_form_header_text(self):
        """Return the header text of the login or register form."""
        return self.browser.find_element_by_css_selector("h6.header").text

    def get_navbar_logout_link(self):
        """Find the logout link on the page."""
        try:
            return self.browser.find_element_by_xpath(
                "//a[contains(., 'Sign Out')]"
            )
        except NoSuchElementException:
            return None

    def try_register(self):
        """Try fill out the registration form."""
        email_input = wait_for_visible(self.browser, "input[name='email']")
        username_input = \
            self.browser.find_element_by_css_selector("input[name='username']")
        password_input = \
            self.browser.find_element_by_css_selector("input[name='password']")
        email_input.send_keys(self.TEST_EMAIL)
        username_input.send_keys(self.TEST_USERNAME)
        password_input.send_keys(self.TEST_PASSWORD)
        recaptcha_iframe = wait_for_visible(
            self.browser,
            # pylint: disable=line-too-long
            xpath_selector="//iframe[contains(@src, 'recaptcha') and @role = 'presentation']"
        )
        self.browser.switch_to.frame(recaptcha_iframe)
        self.browser.find_element_by_id("recaptcha-anchor").click()
        wait_for_visible(self.browser, "span.recaptcha-checkbox-checked")
        self.browser.switch_to.parent_frame()
        submit_button = \
            self.browser.find_element_by_xpath("//input[@name='submit']")
        submit_button.click()

    def assert_user_is_logged_in(self):
        """Asset the user is logged in."""
        self.assertIsNotNone(
            self.get_navbar_logout_link(),
            "Sign out link should exist if the user is logged in"
        )

    def assert_user_is_not_logged_in(self):
        """Assert that the user is not logged in."""
        self.assertIsNone(
            self.get_navbar_logout_link(),
            "Sign out link should not exist if the user is not logged in"
        )

    def test_authentication(self):
        """Test the authentication logic."""
        with self.subTest("A user cannot login without an account"):
            self.browser.get(self.url_for("auth_bp.login"))
            try_fill_out_and_submit_login_form(self.browser,
                                               self.TEST_EMAIL,
                                               self.TEST_PASSWORD)
            self.assert_user_is_not_logged_in()
            self.assertIn("Unrecognised email or password",
                          self.get_invalid_feedback())

        with self.subTest("A user can register an account"):
            register_link = \
                self.browser.find_element_by_css_selector("a.register-link")
            register_link.click()
            self.assertIn("Sign up for Animeu",
                          self.get_form_header_text())
            self.try_register()

        with self.subTest("After registering the user is logged in"):
            self.assert_user_is_logged_in()
            session_cookie = self.browser.get_cookie("session")
            self.assertIsNotNone(
                session_cookie,
                "A session cookie should have been set"
            )

        with self.subTest("The user can then sign out"):
            self.get_navbar_logout_link().click()
            self.assertIn("Login to Animeu", self.get_form_header_text())

        with self.subTest("A user cannot register again with the same email"):
            self.browser.get(self.url_for("auth_bp.register"))
            self.try_register()
            self.assertIn("Email is already registered",
                          self.get_invalid_feedback())

        with self.subTest("Unauthenticated users are redirected to login"):
            self.browser.get(self.url_for("profile_bp.profile"))
            self.assertIn("Login to Animeu", self.get_form_header_text())

        with self.subTest("The user can login and is taken to previous page"):
            perform_login_expecting_success(self.browser,
                                            self.TEST_EMAIL,
                                            self.TEST_PASSWORD)
            self.assert_user_is_logged_in()
            profile_el = self.browser.find_element_by_class_name("profile")
            self.assertIsNotNone(profile_el,
                                 "Expected to be on the profile page.")


class BattleTests(AnimeuIntegrationTestCase):
    """Test the battle page."""

    TEST_EMAIL = "tester@gmail.com"
    TEST_PASSWORD = "password123"

    def get_left_card(self):
        """Get the lefhand card element."""
        return self.browser.find_element_by_css_selector("#left.card")

    def get_right_card(self):
        """Get the righthand card element."""
        return self.browser.find_element_by_css_selector("#right.card")

    @staticmethod
    def get_gallery_image_visibilities(card):
        """Get the visibilities of the gallery images of a card."""
        gallery_images = \
            card.find_elements_by_css_selector(".pictures-grid > img")
        return [img.is_displayed() for img in gallery_images]

    @staticmethod
    def get_chard_character_name(card):
        """Get the name of a character on a card."""
        return card.find_element_by_class_name("english-name").text

    # pylint: disable=too-many-locals,too-many-statements
    def test_battle(self):
        """Test the battle functionality."""
        from animeu.app import db
        from animeu.models import User, FavouritedWaifu, WaifuPickBattle
        from animeu.auth.logic import hash_password

        with self.server_thread.app.app_context():
            user = User(
                email=BattleTests.TEST_EMAIL,
                username="username",
                is_admin=False,
                password_hash=hash_password(BattleTests.TEST_PASSWORD)
            )
            db.session.add(user)
            db.session.commit()
            user = User.query.get(user.id)

            self.browser.get(self.url_for("auth_bp.login"))
            perform_login_expecting_success(self.browser,
                                            BattleTests.TEST_EMAIL,
                                            BattleTests.TEST_PASSWORD)
            self.browser.get(self.url_for("battle_bp.battle"))
            wait_for_visible(self.browser, ".battle-grid")

            # pylint: disable=line-too-long
            with self.subTest("All gallery images shouldn't be visible at first"):
                left_card = self.get_left_card()
                self.assertIn(False,
                              self.get_gallery_image_visibilities(left_card))

            with self.subTest("After expanding the gallery all images are visible"):
                left_card = self.get_left_card()
                # pylint: disable=line-too-long
                left_card.find_element_by_class_name("toggle-picture-view").click()
                self.assertNotIn(
                    False,
                    self.get_gallery_image_visibilities(left_card)
                )

            with self.subTest("Can favourite a character"):
                left_card = self.get_left_card()
                # pylint: disable=line-too-long
                left_card.find_element_by_css_selector(".favourite-button").click()
                wait_for_visible(self.browser, "i.fas.fa-heart")
                expected_name = self.get_chard_character_name(left_card)
                favourited_name = db.engine.execute(
                    select([
                        FavouritedWaifu.character_name
                    ])\
                    .where(FavouritedWaifu.id == user.id)
                ).scalar()
                self.assertEqual(expected_name, favourited_name)

            with self.subTest("Can unfavourite a character"):
                left_card = self.get_left_card()
                # pylint: disable=line-too-long
                left_card.find_element_by_css_selector(".favourite-button").click()
                wait_for_visible(self.browser, "i.far.fa-heart")
                favourited_count = db.engine.execute(
                    select([
                        func.count(FavouritedWaifu.id)
                    ])\
                    .where(FavouritedWaifu.id == user.id)
                ).scalar()
                self.assertEqual(0, favourited_count)

            with self.subTest("Can view the characters info"):
                left_card = self.get_left_card()
                expected_name = self.get_chard_character_name(left_card)
                # pylint: disable=line-too-long
                left_card.find_element_by_css_selector(".english-name > a").click()
                wait_for_visible(self.browser, ".info")
                expected_url = self.url_for("info_bp.info",
                                            character_name=expected_name)
                self.assertIn(expected_url, self.browser.current_url)
                self.browser.back()
                wait_for_visible(self.browser, ".battle-grid")


            with self.subTest("Can pick a winner"):
                loser_card = self.get_left_card()
                winner_card = self.get_right_card()
                expected_winner_name = self.get_chard_character_name(winner_card)
                expected_loser_name = self.get_chard_character_name(loser_card)
                winner_card.find_element_by_class_name("proposal-button").click()
                # wait for the next page to load (which implicity means
                # our changes should be saved to the database...)
                wait_for_visible(
                    self.browser,
                    # pylint: disable=line-too-long
                    xpath_selector=f'//h5[@class="english-name" and contains(., "{expected_winner_name}")]',
                    invert=True
                )
                actual_winner, actual_loser = db.engine.execute(
                    select([
                        WaifuPickBattle.winner_name,
                        WaifuPickBattle.loser_name
                    ])\
                    .where(WaifuPickBattle.user_id == user.id)\
                    .order_by(WaifuPickBattle.id.desc())
                ).first()
                self.assertEqual(expected_winner_name, actual_winner)
                self.assertEqual(expected_loser_name, actual_loser)

class AdminToolsTests(AnimeuIntegrationTestCase):
    """Test the admin pages."""

    TEST_EMAIL = "tester@gmail.com"
    TEST_PASSWORD = "password123"

    @staticmethod
    def move_to_admin_tab(browser, title):
        """Navigate to a different admin tab and wait for it to load."""
        browser.find_element_by_xpath(f"//a[contains(., '{title}')]").click()
        wait_for_visible(
            browser,
            xpath_selector=f"//a[contains(@class, 'active') and contains(., '{title}')]"
        )

    @staticmethod
    def maybe_get_number_of_entries_in_table(browser):
        """Try get the number of entries in the currently visible table."""
        try:
            maybe_pagination_info = \
                browser.find_element_by_css_selector("div.dataTables_info")
            if not maybe_pagination_info:
                return None
            match = re.search(r"\sof\s(?P<total>[\d,]+)\s",
                              maybe_pagination_info.text)
            if not match:
                return None
            total_text = match.group("total")
            return int(total_text.replace(",", ""))
        except NoSuchElementException:
            return None

    @staticmethod
    def iter_current_table_values(browser):
        """Get the current values in the table."""
        for row in browser.find_elements_by_css_selector("tr"):
            cells = row.find_elements_by_css_selector("td")
            yield tuple(c.text for c in cells)

    def assert_all_sort_controls_work_in_table(self):
        """Try out all the sorting controls in the table."""
        for tab in self.browser.find_elements_by_css_selector("th.sorting"):
            for _ in range(2):
                tab.click()
                try:
                    wait_for_visible(
                        self.browser,
                        # pylint: disable=line-too-long
                        xpath_selector="//div[@class = 'dataTables_processing' and contains(., 'Processing...')]",
                        invert=True
                    )
                except SeleniumTimeoutException:
                    self.fail("The results never finished processing")
                else:
                    # make sure we didn't get a server side error alert!
                    try:
                        self.wait.until(expect.alert_is_present())
                        self.fail("An alert was raised")
                    except (SeleniumTimeoutException, expect.NoAlertPresentException):
                        continue

    def perform_action_and_assert_completed(self):
        """Perform the current admin action and expect it to complete."""
        self.browser.find_element_by_css_selector("button.perform-action").click()
        completed_progress_bar = wait_for_visible(
            self.browser,
            xpath_selector="//div[contains(@class, 'progress-bar') and contains(@style, '100%')]",
            timeout=90
        )
        self.assertIsNotNone(
            completed_progress_bar,
            "A completed progress bar should be shown."
        )
        disabled_completed_btn = \
            self.browser.find_element_by_css_selector(
                "button.perform-action:disabled"
            )
        self.assertIsNotNone(
            disabled_completed_btn,
            "The perform action button should be disabled."
        )
        self.assertIn("Complete", disabled_completed_btn.text)

    # pylint: disable=too-many-locals
    def test_admin_tools(self):
        """Test the battle functionality."""
        from animeu.app import db
        from animeu.models import \
            User, FavouritedWaifu, WaifuPickBattle, ELORankingCalculation
        from animeu.auth.logic import hash_password

        with self.server_thread.app.app_context():
            user = User(
                email=AdminToolsTests.TEST_EMAIL,
                username="username",
                is_admin=True,
                password_hash=hash_password(AdminToolsTests.TEST_PASSWORD)
            )
            db.session.add(user)
            db.session.commit()
            user = User.query.get(user.id)

            self.browser.get(self.url_for("auth_bp.login"))
            perform_login_expecting_success(self.browser,
                                            AdminToolsTests.TEST_EMAIL,
                                            AdminToolsTests.TEST_PASSWORD)
            self.browser.find_element_by_xpath("//a[contains(., 'Admin')]").click()
            wait_for_visible(self.browser, ".admin-page")

            with self.subTest("Can seed database with battles"):
                self.move_to_admin_tab(self.browser, "Battles")
                self.perform_action_and_assert_completed()
                self.browser.refresh()
                number_of_entries = \
                    self.maybe_get_number_of_entries_in_table(self.browser)
                self.assertIsNotNone(
                    number_of_entries,
                    "Could not find the table summary information."
                )
                self.assertGreaterEqual(1000, number_of_entries)
                db_entry_count = db.engine.execute(
                    select([
                        func.count(WaifuPickBattle.id)
                    ])
                ).scalar()
                self.assertEqual(number_of_entries, db_entry_count)

        with self.subTest("Can use all the sorting controls"):
            self.assert_all_sort_controls_work_in_table()

        with self.subTest("Can generate the ELO rankings"):
            self.move_to_admin_tab(self.browser, "ELO")
            self.perform_action_and_assert_completed()
            self.browser.refresh()
            rankings_count = db.engine.execute(
                select([
                    func.count(ELORankingCalculation.id)
                ])
            ).scalar()
            self.assertEqual(1, rankings_count)

        with self.subTest("Can see users table"):
            self.move_to_admin_tab(self.browser, "Users")
            self.assert_all_sort_controls_work_in_table()

        with self.subTest("Can see favourited waifus"):
            db.session.add(FavouritedWaifu(
                user_id=user.id,
                date=datetime.now(),
                character_name="Tim",
                order=1
            ))
            db.session.commit()
            self.move_to_admin_tab(self.browser, "Favourited Waifus")
            tims_name = self.browser.find_element_by_xpath(
                "//td[contains(., 'Tim')]"
            )
            self.assertIsNotNone(
                tims_name,
                "Expected to find the favourited 'Tim' in table"
            )

        with self.subTest("Can delete favourited character"):
            self.browser.find_element_by_css_selector("button.delete-button").click()
            wait_for_visible(self.browser, "button.delete-button", invert=True)
            favourited_characters_count = db.engine.execute(
                select([
                    func.count(FavouritedWaifu.id)
                ])
            ).scalar()
            self.assertEqual(0, favourited_characters_count)

class FeedPageTests(AnimeuIntegrationTestCase):
    """Test the feed page."""

    TEST_EMAIL = "tester@gmail.com"
    TEST_PASSWORD = "password123"

    @staticmethod
    def insert_elo_calculation(num_ratings=5):
        """Insert some test ELO ranking data."""
        from animeu.app import db
        from animeu.models import ELORankingCalculation, WaifuPickBattle
        from animeu.data_loader import load_character_data
        characters = \
            [random.choice(load_character_data()) for i in range(num_ratings)]
        rankings = \
            {c["names"]["en"][0]: 100 * i for i, c in enumerate(characters)}
        latest_battle_id = \
            db.engine.execute(select([func.max(WaifuPickBattle.id)])).scalar()
        db.session.add(ELORankingCalculation(
            date=datetime.now(),
            latest_battle_id=latest_battle_id,
            rankings=json.dumps(rankings),
            algorithim_hash="made up"
        ))
        db.session.commit()

    @staticmethod
    def change_leaderboard(browser, name):
        """Change to a ceartin leaderboard."""
        browser.find_element_by_class_name("dropdown-toggle").click()
        browser.find_element_by_xpath(
            f"//a[@class = 'dropdown-item' and contains(., '{name}')]"
        ).click()
        wait_for_visible(
            browser,
            xpath_selector=f"//button[@id = 'leaderboard-dropdown' and contains(., '{name}')]"
        )

    def assert_results_are_visible_in_feed(self):
        """Assert that results are visible in the feed."""
        num_battles = \
            len(self.browser.find_elements_by_class_name("battlecard"))
        self.assertGreater(num_battles, 0)
        num_entries = len(self.browser.find_elements_by_class_name("entry"))
        self.assertGreater(num_entries, 0)


    def test_feed_page(self):
        """Test the feed functionality."""
        from animeu.app import db
        from animeu.models import User, WaifuPickBattle
        from animeu.auth.logic import hash_password
        from animeu.data_loader import load_character_data

        with self.server_thread.app.app_context():
            user = User(
                email=FeedPageTests.TEST_EMAIL,
                username="username",
                is_admin=True,
                password_hash=hash_password(FeedPageTests.TEST_PASSWORD)
            )
            db.session.add(user)
            db.session.commit()
            user = User.query.get(user.id)

            characters = load_character_data()[:10]
            for winner in characters:
                for loser in characters:
                    if winner == loser:
                        continue
                    db.session.add(WaifuPickBattle(
                        user_id=user.id,
                        date=datetime.now(),
                        winner_name=winner["names"]["en"][0],
                        loser_name=loser["names"]["en"][0]
                    ))
                    db.session.commit()
            self.insert_elo_calculation(num_ratings=10)
            db.session.commit()

            with self.subTest("The default feed page shows results"):
                self.browser.get(self.url_for("feed_bp.feed"))
                self.assert_results_are_visible_in_feed()

            with self.subTest("Can view the lowest ELO page"):
                self.change_leaderboard(self.browser, "Lowest ELO")
                self.assert_results_are_visible_in_feed()

            with self.subTest("Can view the top waifus page"):
                self.change_leaderboard(self.browser, "Top Waifus")
                self.assert_results_are_visible_in_feed()

            with self.subTest("Can view the active waifus page"):
                self.change_leaderboard(self.browser, "Active Waifus")
                self.assert_results_are_visible_in_feed()

class ApiTests(AnimeuIntegrationTestCase):
    """Test the API functionality."""

    ADMIN_TEST_EMAIL = "tester@gmail.com"
    ADMIN_TEST_PASSWORD = "password123"
    NON_ADMIN_TEST_EMAIL = "iamnoadmin@gmail.com"
    NON_ADMIN_TEST_PASSWORD = "password123"

    @classmethod
    # pylint: disable=arguments-differ
    def setUpClass(cls, *args, **kwargs):
        """Initialize the test class."""
        super().setUpClass(*args, with_browser=False, **kwargs)

    def test_api(self):
        """Test the API."""
        from animeu.app import db
        from animeu.models import User
        from animeu.auth.logic import hash_password

        with self.server_thread.app.app_context():
            admin_user = User(
                email=ApiTests.ADMIN_TEST_EMAIL,
                username="adminuser",
                is_admin=True,
                password_hash=hash_password(ApiTests.ADMIN_TEST_PASSWORD)
            )
            non_admin_user = User(
                email=ApiTests.NON_ADMIN_TEST_EMAIL,
                username="notanadminuser",
                is_admin=False,
                password_hash=hash_password(ApiTests.NON_ADMIN_TEST_PASSWORD)
            )
            db.session.add(admin_user)
            db.session.add(non_admin_user)
            db.session.commit()
            admin_user = User.query.get(admin_user.id)
            non_admin_user = User.query.get(non_admin_user.id)


            with self.subTest("Non admin user cannot get an API key"):
                response = requests.get(
                    self.url_for("api_bp.get_api_token"),
                    auth=requests.auth.HTTPBasicAuth(
                        ApiTests.NON_ADMIN_TEST_EMAIL,
                        ApiTests.NON_ADMIN_TEST_PASSWORD
                    )
                )
                self.assertEqual(HTTPStatus.UNAUTHORIZED, response.status_code)
                non_admin_user = User.query.get(non_admin_user.id)
                self.assertFalse(non_admin_user.api_token,
                                 "No API token should have been created")

            admin_token = None

            with self.subTest("Admin user can request an API key"):
                response = requests.get(
                    self.url_for("api_bp.get_api_token"),
                    auth=requests.auth.HTTPBasicAuth(
                        ApiTests.ADMIN_TEST_EMAIL,
                        ApiTests.ADMIN_TEST_PASSWORD
                    )
                )
                admin_token = response.text
                self.assertEqual(HTTPStatus.OK, response.status_code)
                self.assertTrue(admin_token, "Token should have been returned")
                admin_user = User.query.get(admin_user.id)
                self.assertTrue(admin_user.api_token,
                                "API token should have been created")

            with self.subTest("Cannot access character API without token"):
                response = \
                    requests.get(self.url_for("api_bp.paginate_characters"))
                self.assertEqual(HTTPStatus.UNAUTHORIZED, response.status_code)

            with self.subTest("Can access character API with token"):
                response = requests.get(
                    self.url_for("api_bp.paginate_characters"),
                    params={"limit": "1",
                            "anime": r"Akame?",
                            "name": r"[aA]kame?",
                            "tag": "stoic",
                            "description": "Night Raid"},
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                self.assertEqual(HTTPStatus.OK, response.status_code)
                response_json = response.json()
                self.assertEqual(1,
                                 len(response_json["characters"]),
                                 "Expected a single result")
                self.assertEqual(
                    "Akame",
                    response_json["characters"][0]["names"]["en"][0]
                )
