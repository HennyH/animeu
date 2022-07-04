# /animeu/common/file_helpers.py
#
# Helpers for dealing with files.
#
# See /LICENCE.md for Copyright information
"""Helpers for dealing with files."""
import sys
import codecs
import re
import json
from contextlib import contextmanager

import cchardet as chardet

# pylint: disable=too-many-arguments
@contextmanager
def open_transcoded(filename,
                    mode,
                    source_enc=None,
                    target_enc="utf8",
                    errors="strict",
                    fallback_enc="utf8",
                    detect_buffer_size=50 * int(10e6)):
    """Open a file and transcode the content on the fly."""
    # ensure we open the file in a binary mode
    binary_mode = re.sub(r"([^b+]+)(?:b)?([+]?)", r"\1b\2", mode)
    if source_enc is None:
        # pylint: disable=broad-except
        try:
            # pylint: disable=unspecified-encoding
            with open(filename, "rb") as file_obj:
                data = file_obj.read(detect_buffer_size)
            source_enc = chardet.detect(data)["encoding"]
            del data
        except Exception as error:
            print("""Warning: an error occured while trying to guess the """
                  f"""encoding of the file '{filename}', will assume """
                  f"""{fallback_enc} encoding: {error}.""",
                  file=sys.stderr)
            source_enc = fallback_enc
    # pylint: disable=unspecified-encoding
    with open(filename, binary_mode) as stream:
        with codecs.EncodedFile(stream,
                                target_enc,
                                file_encoding=source_enc,
                                errors=errors) as recorder:
            yield recorder


class JSONListStream():
    """A context-manager class to stream json objects to a file."""

    def __init__(self, fileobj):
        """Initialize this JSONListStream with fileobj."""
        # pylint: disable=super-with-arguments
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
