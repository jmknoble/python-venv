"""Provide class model for venv virtual environments."""

import os
import os.path
import shutil
import stat
import sys

from .. import const, exceptions, reqs, runcommand
from .base import BaseVirtualEnvironment

####################


class VenvEnvironment(BaseVirtualEnvironment):
    """Model a Python3 `venv`:py:mod: virtual environment."""

    @property
    def env_name(self):
        """Get the name for this environment."""
        if self._env_name is None:
            self._env_name = const.VENV_DIR
        return self._env_name

    @property
    def env_description(self):
        """Get a textual description of this environment."""
        if self._env_description is None:
            self._env_description = f"Python venv at {self.env_dir}"
        return self._env_description

    def env_exists(self):
        """Tell whether this environment already exists."""
        if os.path.isdir(self.env_dir):
            return True
        if os.path.exists(self.env_dir):
            raise exceptions.EnvOccludedError(
                f"{self.abs_env_dir} exists, but is not a directory"
            )
        return False

    def check_preexisting(self):
        """Check for a pre-existing environment."""
        if self.env_exists():
            raise exceptions.EnvExistsError(f"Found preexisting {self.env_dir}")

    def do_create(self):
        """Create this environment."""
        runcommand.run_command(
            [self.python, "-m", "venv", self.env_dir],
            show_trace=True,
            dry_run=self.dry_run,
            env=self.os_environ,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        verb = "Would have created" if self.dry_run else "Created"
        self.progress(f"{verb} {self.abs_env_dir}", suffix=None)

        self.env_activate = os.path.join(self.env_bin_dir, "activate")

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
                f"To use your virtual environment: 'source {self.env_activate}'."
            )

    def do_remove(self):
        """Remove this environment."""
        if not self.env_exists():
            self.progress(f"Good news!  There is no {self.env_description}.")
            return

        def _retry_readonly(func, path, _excinfo):
            """Make file writable and attempt to remove again."""
            os.chmod(path, stat.S_IWRITE)
            func(path)

        verb = "Would remove" if self.dry_run else "Removing"
        self.progress(f"{verb} {self.abs_env_dir} and all its contents")

        if not self.dry_run:
            shutil.rmtree(self.env_dir, onerror=_retry_readonly)
