"""Provide class model for conda virtual environments."""

import os
import os.path
import sys

from .. import const, exceptions, runcommand
from .base import BaseVirtualEnvironment

####################


class CondaEnvironment(BaseVirtualEnvironment):
    """
    Model a ``conda`` virutal environment.

    Args:
        python_version
            A string containing the version of the Python interpreter to place
            into the resulting environment (default: ``"3"``).

    See Also:
        base/parent class
    """

    def __init__(self, *args, **kwargs):
        self.python_version = kwargs.pop("python_version", None)
        if self.python_version is None:
            self.python_version = "3"
        super(CondaEnvironment, self).__init__(*args, **kwargs)

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

    @property
    def env_dir(self):
        """Get the directory where this environment lives."""
        if self.have_env_prefix():
            return os.path.join(self.env_prefix, self.env_name)

        try:
            env_dir = self.get_conda_env_dir()
            return env_dir
        except exceptions.EnvNotFoundError:
            if self.dry_run:
                return const.ENV_DIR_PLACEHOLDER
            raise

    def get_conda_env_dir(self):
        """Get the directory where this environment lives, if conda manages it."""
        env_listing = runcommand.run_command(
            [const.CONDA, "env", "list"],
            return_output=True,
            show_trace=False,
            dry_run=False,
            env=self.os_environ,
        ).splitlines()

        for line in (x.strip() for x in env_listing):  # generator expression
            if line.startswith("# ") or not line:
                continue
            parts = line.split(maxsplit=1)
            if len(parts) < 2:
                continue
            if parts[0] == self.env_name:
                env_dir = parts[1]
                if env_dir.startswith("* "):
                    env_dir = env_dir.split(maxsplit=1)[1]
                return env_dir

        raise exceptions.EnvNotFoundError(
            f"unable to find conda environment {self.env_name}"
        )

    @property
    def env_description(self):
        """Get a textual description of this environment."""
        if self._env_description is None:
            self._env_description = f"conda environment {self.env_name}"
        return self._env_description

    def env_exists(self):
        """Tell whether this environment already exists."""
        if not self.have_env_prefix():
            try:
                self.get_conda_env_dir()
            except exceptions.EnvNotFoundError:
                return False
            return True
        if os.path.isdir(self.env_dir):
            return True
        if os.path.exists(self.env_dir):
            raise exceptions.EnvOccludedError(
                f"{self.env_dir} exists, but is not a directory"
            )
        return False

    def check_preexisting(self):
        """Check for a pre-existing environment."""
        if self.env_exists():
            raise exceptions.EnvExistsError(f"Found preexisting {self.env_name}")

    def do_create(self):
        """Create this environment."""
        conda_command = [const.CONDA, "create", "--quiet"]
        if self.force:
            conda_command.append("--yes")
        if self.have_env_prefix():
            conda_command.extend(["-p", self.abs_env_dir])
        else:
            conda_command.extend(["-n", self.env_name])
        runcommand.run_command(
            conda_command + [f"python={self.python_version}"],
            show_trace=True,
            dry_run=self.dry_run,
            env=self.os_environ,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

        self.progress(f"Installing {self.req_scheme} requirements")

        self.requirements.use_python(self.env_python)
        self.requirements.stdout = sys.stdout  # required for testing ...
        self.requirements.stderr = sys.stderr  # ... or capturing output
        self.requirements.fulfill()

    def suggest_activate(self):
        """Suggest how to activate the environment."""
        if not self.dry_run:
            self.progress(
                f"To use your virtual environment: 'conda activate {self.env_name}'."
            )

    def do_remove(self):
        """Remove this environment."""
        if not self.env_exists():
            self.progress(f"Good news!  There is no {self.env_description}.")
            return

        conda_command = [const.CONDA, "env", "remove", "--quiet"]
        if self.force:
            conda_command.append("--yes")
        if self.have_env_prefix():
            conda_command.extend(["-p", self.abs_env_dir])
        else:
            conda_command.extend(["-n", self.env_name])
        runcommand.run_command(
            conda_command,
            show_trace=True,
            dry_run=self.dry_run,
            env=self.os_environ,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
