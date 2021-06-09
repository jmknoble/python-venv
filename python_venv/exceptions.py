"""Provide exception classes for `~python_venv`:py:mod:."""


class BaseError(Exception):
    """Base exception."""

    pass


class EnvError(BaseError):
    """Base exception for environments."""

    pass


class RequirementsError(BaseError):
    """Base exception for requirements."""

    pass


class EnvNotFoundError(EnvError):
    """A virtual environment was expected to exist, but does not."""

    pass


class EnvExistsError(EnvError):
    """A virtual environment was expected not to exist, but does."""

    pass


class EnvOccludedError(EnvError):
    """Something else is in the way of a virtual environment."""

    pass


class MissingRequirementsError(RequirementsError):
    """One or more source of requirements is expected but missing."""

    pass
