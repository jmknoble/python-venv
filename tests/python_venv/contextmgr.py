"""Provide context managers for use in unit tests."""

import contextlib
import sys
from io import StringIO


@contextlib.contextmanager
def capture(a_callable, *args, **kwargs):
    """Capture status, stdout, and stderr from a function or method call"""
    (orig_stdout, sys.stdout) = (sys.stdout, StringIO())
    (orig_stderr, sys.stderr) = (sys.stderr, StringIO())
    try:
        status = a_callable(*args, **kwargs)
        sys.stdout.seek(0)
        sys.stderr.seek(0)
        yield (status, sys.stdout.read(), sys.stderr.read())
    finally:
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = orig_stdout
        sys.stderr = orig_stderr
