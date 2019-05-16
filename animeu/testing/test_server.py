# /animeu/testings/test_server.py
#
# Utilities for launching a server for testing purposes.
#
# See /LICENCE.md for Copyright information
"""Utilities for launching a server for testing purposes."""
import threading
import urllib.request as request
from urllib.error import URLError
import time

import coverage
from cheroot import wsgi

class ServerThread(threading.Thread):
    """Run a server in a seperate thread."""

    def __init__(self, *args, **kwargs):
        """Initialize a new ServerThread."""
        super().__init__(*args, **kwargs)
        from animeu.app import app
        self.app = app
        self.server = wsgi.Server(('0.0.0.0', 5000), self.app, max=1)
        self.started_event = threading.Event()

    def is_server_ready(self):
        """Check if the server is ready to respond to to requests."""
        return self.started_event.is_set()

    def wait_till_server_ready(self,
                               wait_timeout=30,
                               poll_timeout=5,
                               sleep_time=2):
        """Wait untill the server is ready or the timeout expires."""
        if self.is_server_ready():
            return
        wait_time = 0
        while wait_time < wait_timeout:
            try:
                request.urlopen("http://localhost:5000", timeout=poll_timeout)
                self.started_event.set()
                return
            except (TimeoutError, URLError) as ex:
                time.sleep(sleep_time)
                wait_time += poll_timeout + sleep_time
        raise TimeoutError("""Server was not ready in time.""")

    def run(self):
        """Start up the server."""
        coverage.process_startup()
        with self.app.app_context():
            from flask_migrate import upgrade
            upgrade()
        self.server.start()

    def shutdown(self):
        """Shutdown the server."""
        self.server.stop()
