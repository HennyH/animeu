# /animeu/testings/integration_tests.py
#
# Integration tests for the animeu site.
#
# See /LICENCE.md for Copyright information
"""Integration tests for the animeu site."""
import os
import unittest
from tempfile import mkstemp

from sqlalchemy.sql import select
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
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
    def setUpClass(cls):
        """Set up a test environment."""
        if os.path.exists(AnimeuIntegrationTestCase.__TEST_DATABASE_FILENAME):
            os.unlink(AnimeuIntegrationTestCase.__TEST_DATABASE_FILENAME)
        os.environ["COVERAGE_PROCESS_START"] = ".coveragerc"
        os.environ["DATABASE"] = os.environ.get(
            "TEST_DATABASE_URL",
            f"sqlite:///{AnimeuIntegrationTestCase.__TEST_DATABASE_FILENAME}"
        )
        headless = "NO_HEADLESS" not in os.environ
        cls.browser = \
            webdriver.Chrome(options=get_chrome_options(headless=headless))
        cls.wait = WebDriverWait(cls.browser, 10)
        from animeu.app import app
        cls.server_thread = ServerThread(app)
        cls.server_thread.start()
        cls.server_thread.wait_till_server_ready()
        cls.url_for = cls.server_thread.url_for

    @classmethod
    def tearDownClass(cls):
        """Tear down the environment."""
        cls.server_thread.shutdown()
        cls.server_thread.join()
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
        with self.subTest("Unauthenticated users are redirected to login"):
            self.browser.get(self.url_for("auth_bp.login"))
            self.assertIn("Login to Animeu", self.get_form_header_text())

        with self.subTest("A user cannot login without an account"):
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

        with self.subTest("The user can login normally"):
            self.browser.get(self.url_for("auth_bp.login"))
            perform_login_expecting_success(self.browser,
                                            self.TEST_EMAIL,
                                            self.TEST_PASSWORD)
            self.assert_user_is_logged_in()

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

    # pylint: disable=too-many-locals
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
            wait_for_visible(self.browser, ".card")

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
