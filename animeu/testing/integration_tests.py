# /animeu/testings/integration_tests.py
#
# Integration tests for the animeu site.
#
# See /LICENCE.md for Copyright information
"""Integration tests for the animeu site."""
import os
import unittest

from selenium import webdriver

from animeu.testing.test_server import ServerThread

def get_chrome_options(headless=True):
    """Get a default set of options to launch headless chrome."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("headless")
    options.add_argument("window-size=1920x1080")
    options.add_argument("start-maximized")
    return options

class SignupTests(unittest.TestCase):
    """Test the signup and signin functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up the environment."""
        os.environ["COVERAGE_PROCESS_START"] = ".coveragerc"
        os.environ["DATABASE"] = \
            os.environ.get("TEST_DATABASE_URL", "sqlite://")
        cls.browser = webdriver.Chrome(options=get_chrome_options())
        cls.server_thread = ServerThread()
        cls.server_thread.start()
        cls.server_thread.wait_till_server_ready()

    @classmethod
    def tearDownClass(cls):
        """Tear down the environment."""
        cls.server_thread.shutdown()
        cls.server_thread.join()
        cls.browser.quit()

    def test_register_and_signin(self):
        """Test we can register and sign in."""
        self.browser.get("http://localhost:5000")
