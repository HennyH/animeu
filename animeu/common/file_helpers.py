# /animeu/common/file_helpers.py
#
# Helpers for dealing with files.
#
# See /LICENCE.md for Copyright information
"""Helpers for dealing with files."""
import sys
import codecs
import re
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
            with open(filename, "rb") as file_obj:
                data = file_obj.read(detect_buffer_size)
            source_enc = chardet.detect(data)["encoding"]
            del data
        except Exception as error:
            print("""Warning: an error occured while trying to guess the """
                  """encoding of the file '{filename}', will assume """
                  """{fallback} encoding: {message}.""".format(
                      filename=filename,
                      fallback=fallback_enc,
                      message=str(error)
                  ),
                  file=sys.stderr)
            source_enc = fallback_enc
    with open(filename, binary_mode) as stream:
        with codecs.EncodedFile(stream,
                                target_enc,
                                file_encoding=source_enc,
                                errors=errors) as recorder:
            yield recorder
