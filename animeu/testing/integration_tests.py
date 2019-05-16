# /animeu/testings/integration_tests.py
#
# Integration tests for the animeu site.
#
# See /LICENCE.md for Copyright information
"""Integration tests for the animeu site."""
import os
import unittest
import time
from tempfile import mktemp

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

class AuthenticationTests(unittest.TestCase):
    """Test the signup and login/logout functionality."""

    INDEX_URL = "http://localhost:5001/"
    LOGIN_URL = "http://localhost:5001/login"
    REGISTER_URL = "http://localhost:5001/register"
    TEST_EMAIL = "test@gmail.com"
    TEST_USERNAME = "iamuser"
    TEST_PASSWORD = "password123"
    TEST_PASSWORD_TOO_SHORT = "pw"

    @classmethod
    def setUpClass(cls):
        """Set up the environment."""
        cls.db_filename = mktemp()
        os.environ["COVERAGE_PROCESS_START"] = ".coveragerc"
        os.environ["DATABASE"] = os.environ.get(
            "TEST_DATABASE_URL",
            f"sqlite:///{cls.db_filename}"
        )
        headless = "NO_HEADLESS" not in os.environ
        cls.browser = \
            webdriver.Chrome(options=get_chrome_options(headless=headless))
        cls.wait = WebDriverWait(cls.browser, 10)
        cls.server_thread = ServerThread()
        cls.server_thread.start()
        cls.server_thread.wait_till_server_ready()

    @classmethod
    def tearDownClass(cls):
        """Tear down the environment."""
        cls.server_thread.shutdown()
        cls.server_thread.join()
        cls.browser.quit()
        if os.path.exists(cls.db_filename):
            os.unlink(cls.db_filename)

    def try_sign_in(self):
        """Assume we're on the login page and try sign in."""
        email_input = \
            self.browser.find_element_by_xpath("//input[@name='email']")
        password_input = \
            self.browser.find_element_by_xpath("//input[@name='password']")
        email_input.send_keys(self.TEST_EMAIL)
        password_input.send_keys(self.TEST_PASSWORD)
        submit_button = \
            self.browser.find_element_by_xpath("//input[@name='submit']")
        submit_button.click()

    def get_invalid_feedback(self):
        """Get a string of any invalid feedback on the page."""
        invalid_feedback_els = \
            self.browser.find_elements_by_class_name("invalid-feedback")
        return "\n".join([e.text for e in invalid_feedback_els])

    def get_form_header_text(self):
        """Return the header text of the login or register form."""
        return self.browser.find_element_by_css_selector("h6.header").text

    def try_register(self):
        """Try fill out the registration form."""
        email_input = \
            self.browser.find_element_by_xpath("//input[@name='email']")
        username_input = \
            self.browser.find_element_by_xpath("//input[@name='username']")
        password_input = \
            self.browser.find_element_by_xpath("//input[@name='password']")
        email_input.send_keys(self.TEST_EMAIL)
        username_input.send_keys(self.TEST_USERNAME)
        password_input.send_keys(self.TEST_PASSWORD)
        recaptcha_iframe = self.wait.until(
            expect.visibility_of_element_located(
                # pylint: disable=line-too-long
                (By.XPATH, "//iframe[contains(@src, 'recaptcha') and @role = 'presentation']")
            )
        )
        self.browser.switch_to.frame(recaptcha_iframe)
        self.browser.find_element_by_id("recaptcha-anchor").click()
        time.sleep(5)
        self.browser.switch_to.parent_frame()
        submit_button = \
            self.browser.find_element_by_xpath("//input[@name='submit']")
        submit_button.click()

    def get_navbar_logout_link(self):
        """Find the logout link on the page."""
        try:
            return self.browser.find_element_by_xpath(
                "//a[contains(., 'Sign Out')]"
            )
        except NoSuchElementException:
            return None

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
        self.browser.implicitly_wait(5)

        with self.subTest("Unauthenticated users are redirected to login"):
            self.browser.get(self.INDEX_URL)
            self.assertIn("Login to Animeu", self.get_form_header_text())

        with self.subTest("A user cannot login without an account"):
            self.try_sign_in()
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
            self.browser.get(self.REGISTER_URL)
            self.try_register()
            self.assertIn("Email is already registered",
                          self.get_invalid_feedback())

        with self.subTest("The user can login normally"):
            self.browser.get(self.LOGIN_URL)
            self.try_sign_in()
            self.assert_user_is_logged_in()
