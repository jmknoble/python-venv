"""Provide exception classes for `~python_venv`:py:mod:."""


class EnvNotFoundError(Exception):
    """A virtual environment was expected to exist, but does not."""

    pass
