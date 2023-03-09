"""Provide class model for pyenv virtual environments."""

import subprocess
import sys

from .. import const, exceptions, reqs, runcommand
from .base import BaseVirtualEnvironment

####################


class PyenvEnvironment(BaseVirtualEnvironment):
    """
    Model a `pyenv-virtualenv`_ virtual environment.

    .. _pyenv-virtualenv: https://github.com/pyenv/pyenv-virtualenv

    Args:
        python_version
            A string containing the version of the Python interpreter to place
            into the resulting environment (default: `None`).

    See Also:
        base/parent class
    """

    def __init__(self, *args, **kwargs):
        self.python_version = kwargs.pop("python_version", None)
        super(PyenvEnvironment, self).__init__(*args, **kwargs)

        if self.python_version is not None:
            self.os_environ[const.PYENV_VERSION] = self.python_version

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
            if self.have_env_prefix():
                self._env_name = "".join([self.env_prefix, self._env_name])
        return self._env_name

    @property
    def env_dir(self):
        """Get the directory where this environment lives."""
        try:
            env_dir = self.get_pyenv_env_dir()
            return env_dir
        except exceptions.EnvNotFoundError:
            if self.dry_run:
                return const.ENV_DIR_PLACEHOLDER
            raise

    def get_pyenv_env_dir(self):
        """Get the directory where this environment lives, if pyenv manages it."""
        try:
            env_dir = runcommand.run_command(
                [const.PYENV, "prefix", self.env_name],
                return_output=True,
                show_trace=False,
                dry_run=False,
                env=self.os_environ,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            raise exceptions.EnvNotFoundError(
                f"unable to find pyenv environment {self.env_name}"
            )
        if env_dir.endswith("\n"):
            env_dir = env_dir[:-1]
        return env_dir

    @property
    def env_description(self):
        """Get a textual description of this environment."""
        if self._env_description is None:
            self._env_description = f"pyenv environment {self.env_name}"
        return self._env_description

    def progress_start(self):
        """Emit a progress message when starting any activity."""
        if self.python_version is not None:
            self.progress(f"Setting {const.PYENV_VERSION}={self.python_version}")

    def env_exists(self):
        """Tell whether this environment already exists."""
        try:
            self.get_pyenv_env_dir()
        except exceptions.EnvNotFoundError:
            return False
        return True

    def check_preexisting(self):
        """Check for a pre-existing environment."""
        if self.env_exists():
            raise exceptions.EnvExistsError(f"Found preexisting {self.env_name}")

    def do_create(self):
        """Create this environment."""
        runcommand.run_command(
            [const.PYENV, "virtualenv", self.env_name],
            show_trace=True,
            dry_run=self.dry_run,
            env=self.os_environ,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        verb = "Would have created" if self.dry_run else "Created"
        self.progress(f"{verb} {self.env_name}", suffix=None)

        self.progress(f"Installing {self.req_scheme} requirements")
        venv_requirements = reqs.ReqScheme(
            reqs.REQ_SCHEME_VENV,
            python=self.env_python,
            dry_run=self.dry_run,
            env=self.os_environ,
        )
        venv_requirements.fulfill(upgrade=True)

        self.requirements.use_python(self.env_python)
        self.requirements.stdout = sys.stdout  # required for testing ...
        self.requirements.stderr = sys.stderr  # ... or capturing output
        self.requirements.fulfill()

    def suggest_activate(self):
        """Suggest how to activate the environment."""
        if not self.dry_run:
            self.progress(
                f"To use your virtual environment: 'pyenv activate {self.env_name}'."
            )

    def do_remove(self):
        """Remove this environment."""
        if not self.env_exists():
            self.progress(f"Good news!  There is no {self.env_description}.")
            return

        pyenv_command = [const.PYENV, "virtualenv-delete"]
        if self.force:
            pyenv_command.append("-f")
        pyenv_command.append(self.env_name)
        runcommand.run_command(
            pyenv_command,
            show_trace=True,
            dry_run=self.dry_run,
            env=self.os_environ,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
