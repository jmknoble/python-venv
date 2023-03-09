"""Provide class model for named venv virtual environments."""

from .. import const
from .venv import VenvEnvironment

####################


class NamedVenvEnvironment(VenvEnvironment):
    """
    Model a named Python3 `venv`:py:mod: virtual environment.

    Args:
        env_prefix
            The path to a directory in which to create the virtual environment
            (required).

    See Also:
        base/parent class
    """

    def __init__(self, *args, **kwargs):
        super(NamedVenvEnvironment, self).__init__(*args, **kwargs)

        if not self.have_env_prefix():
            raise ValueError(
                "The 'env_prefix' argument is required and must not be None"
            )

    @property
    def need_setup_py(self):
        """Tell whether a setup.py is necessary."""
        return True  # We always need it for constructing env_name

    @property
    def env_name(self):
        """Get the name for this environment."""
        if self._env_name is None:
            self._env_name = self.basename
            if self.requirements.is_dev():
                self._env_name += const.DEV_SUFFIX
        return self._env_name
