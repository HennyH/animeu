# /nimeu/spiders/json_helpers.py
#
# Helpers for manipulating JSON.
#
# See /LICENCE.md for Copyright information
"""Helpers for manipulating JSON."""

import json


class JSONListStream():
    """A context-manager class to stream json objects to a file."""

    def __init__(self, fileobj):
        """Initialize this JSONListStream with fileobj."""
        super(JSONListStream, self).__init__()
        self._printed_first_entry = False
        self._fileobj = fileobj

    def __enter__(self):
        """Context to start using this JSONListStream."""
        return self.enter()

    def __exit__(self, exc, exc_type, traceback):
        """Context to stop using this JSONListStream."""
        self.exit()

    def enter(self):
        """Start using this JSONListStream, printing the starting character."""
        self._fileobj.write("[")
        return self

    def exit(self):
        """Stop using this JSONListStream, printing the ending character."""
        self._fileobj.write("]")
        return self

    def write(self, entry):
        """Write a new entry to this JSONListStream."""
        if not self._printed_first_entry:
            self._printed_first_entry = True
        else:
            self._fileobj.write(",\n")

        self._fileobj.write(json.dumps(entry))
