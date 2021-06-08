"""Provide class model for virtual environments."""

import os
import os.path
import shutil
import stat

from . import exceptions, reqs, runcommand

PYTHON = "python3"
CONDA = "conda"
VENV_DIR = ".venv"
DEV_SUFFIX = "-dev"

MESSAGE_PREFIX = "==> "

####################


class BaseVirtualEnvironment(object):
    """
    Model an abstract base virtual environment.

    :Args:
        req_scheme
            The requirements scheme from `~python_env.reqs`:py:mod: to use for
            this environment.

        dry_run
            (optional) If `True`-ish, say what would be done rather than doing it.

        force
            (optional) If `True`-ish, avoid any prompts.

        message_prefix
            (optional) The prefix to use when printing progress or feedback messages.

        python
            (optional) The basename of the Python interpreter to use for
            running Python commands.

        basename
            (optional) The basename of the Python project in the current
            directory (default: inferred).

        env_name
            (optional) The name of the virtual environment to create (default:
            inferred).
    """

    def __init__(
        self,
        req_scheme,
        dry_run=False,
        force=False,
        message_prefix=None,
        python=None,
        basename=None,
        env_name=None,
    ):
        self.req_scheme = req_scheme
        self.dry_run = dry_run
        self.force = force
        self.message_prefix = message_prefix
        self.python = python

        self._basename = basename
        self._env_name = env_name

        self._requirements = None
        self._package_name = None
        self._env_description = None

        if self.message_prefix is None:
            self.message_prefix = MESSAGE_PREFIX

        if self.python is None:
            self.python = PYTHON

    def progress(self, message, suffix="..."):
        """Print a progress message."""
        message_parts = [message]
        if suffix and not message.endswith("."):
            message_parts.append(suffix)
        runcommand.print_trace(
            message_parts, trace_prefix=MESSAGE_PREFIX, dry_run=self.dry_run
        )

    @property
    def requirements(self):
        """Get the requirements sources for this environment."""
        if self._requirements is None:
            self._requirements = reqs.requirements_sources_for_scheme(self.req_scheme)
        return self._requirements

    @property
    def package_name(self):
        """Get the package name for the Python project in the current directory."""
        try:
            self._package_name
        except AttributeError:
            self._package_name = None

        if self._package_name is None:
            self._package_name = runcommand.run_command(
                [self.python, "setup.py", "--name"],
                dry_run=False,
                return_output=True,
                show_trace=False,
            )
            if self._package_name.endswith("\n"):
                self._package_name = self._package_name[:-1]
        return self._package_name

    @property
    def basename(self):
        """Get the basename for the Python project in the current directory."""
        if self._basename is None:
            self._basename = self.package_name.replace("_", "-")
        return self._basename

    @property
    def env_name(self):
        """Get the environment name (abstract method)."""
        raise NotImplementedError(
            "This is an abstract base class, please inherit from it."
        )

    def create(self, check_preexisting=True):
        """Create the environment (abstract method)."""
        raise NotImplementedError(
            "This is an abstract base class, please inherit from it."
        )

    def remove(self):
        """Remove the environment (abstract method)."""
        raise NotImplementedError(
            "This is an abstract base class, please inherit from it."
        )

    def replace(self):
        """Replace the environment (abstract method)."""
        raise NotImplementedError(
            "This is an abstract base class, please inherit from it."
        )


####################


class VenvEnvironment(BaseVirtualEnvironment):
    """Model a Python3 `venv`:py:mod: virtual environment."""

    @property
    def env_name(self):
        """Get the name for this environment."""
        if self._env_name is None:
            self._env_name = VENV_DIR
        return self._env_name

    @property
    def env_dir(self):
        """Alias for `~python_venv.env.VenvEnvironment.env_name`:py:attr:."""
        return self.env_name

    @property
    def full_env_dir(self):
        """Get a full path to this environment."""
        return os.path.abspath(self.env_dir)

    @property
    def env_description(self):
        """Get a textual description of this environment."""
        if self._env_description is None:
            self._env_description = f"Python venv at {self.env_name}"
        return self._env_description

    def create(self, check_preexisting=True):
        """Create this environment."""
        self.progress(f"Creating {self.env_description}")

        if os.path.isdir(self.env_dir):
            if not self.dry_run or (self.dry_run and check_preexisting):
                raise exceptions.EnvExistsError(f"Found preexisting {self.env_dir}")
        elif os.path.exists(self.env_dir):
            raise exceptions.EnvOccludedError(
                f"{self.full_env_dir} exists, but is not a directory"
            )

        runcommand.run_command(
            [self.python, "-m", "venv", self.env_dir],
            show_trace=True,
            dry_run=self.dry_run,
        )
        verb = "Would have created" if self.dry_run else "Created"
        self.progress(f"{verb} {self.full_env_dir}", suffix=None)

        env_bin_dir = os.path.join(self.env_dir, "bin")
        env_python = os.path.join(env_bin_dir, self.python)
        env_activate = os.path.join(env_bin_dir, "activate")

        self.progress(f"Installing {self.req_scheme} requirements")

        pip_install_command = [env_python, "-m", "pip", "install"]
        runcommand.run_command(
            pip_install_command + ["--upgrade"] + reqs.requirements_for_venv(),
            show_trace=True,
            dry_run=self.dry_run,
        )

        for command in reqs.command_requirements(self.requirements, python=env_python):
            runcommand.run_command(command, show_trace=True, dry_run=self.dry_run)

        if reqs.requirements_need_pip(self.requirements):
            runcommand.run_command(
                pip_install_command
                + reqs.pip_requirements(self.requirements, self.basename),
                show_trace=True,
                dry_run=self.dry_run,
            )

        self.progress("Done.")
        if not self.dry_run:
            self.progress(f"To use your virtual environment: 'source {env_activate}'.")

    def remove(self):
        """Remove this environment."""
        self.progress(f"Removing {self.env_description}")

        if not os.path.exists(self.env_dir):
            self.progress(f"Good news!  There is no {self.env_description}.")
            return

        if not os.path.isdir(self.env_dir):
            raise exceptions.EnvOccludedError(
                f"{self.full_env_dir} exists, but is not a directory"
            )

        def _retry_readonly(func, path, _excinfo):
            """Make file writable and attempt to remove again."""
            os.chmod(path, stat.S_IWRITE)
            func(path)

        verb = "Would remove" if self.dry_run else "Removing"
        self.progress(f"{verb} {self.full_env_dir} and all its contents")

        if not self.dry_run:
            shutil.rmtree(self.env_dir, onerror=_retry_readonly)

        self.progress("Done.")


####################


class CondaEnvironment(BaseVirtualEnvironment):
    """Model a ``conda`` virutal environment."""

    @property
    def env_name(self):
        """Get the name for this environment."""
        if self._env_name is None:
            self._env_name = self.basename
            if reqs.is_dev_req_scheme(self.req_scheme):
                self._env_name += DEV_SUFFIX
        return self._env_name

    @property
    def env_dir(self):
        """Get the directory where this environment lives."""
        if self.dry_run:
            return "CONDA_ENV_DIR"

        env_listing = runcommand.run_command(
            [CONDA, "env", "list"],
            return_output=True,
            show_trace=False,
            dry_run=self.dry_run,
        ).splitlines()

        for line in (x.strip() for x in env_listing):  # generator expression
            if line.startswith("# ") or not line:
                continue
            parts = line.split(maxsplit=1)
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
        """Tell whether this environment (already?) exists."""
        try:
            self.env_dir
        except exceptions.EnvNotFoundError:
            return False
        return True

    def create(self, check_preexisting=True):
        """Create this environment."""
        self.progress(f"Creating {self.env_description}")

        if self.env_exists() and (
            not self.dry_run or (self.dry_run and check_preexisting)
        ):
            raise exceptions.EnvExistsError(f"Found preexisting {self.env_name}")

        conda_command = [CONDA, "create"]
        if self.force:
            conda_command.append("--yes")
        runcommand.run_command(
            conda_command + ["-n", self.env_name, "python=3"],
            show_trace=True,
            dry_run=self.dry_run,
        )

        env_bin_dir = os.path.join(self.env_dir, "bin")  # raises if not found
        env_python = os.path.join(env_bin_dir, self.python)

        self.progress(f"Installing {self.req_scheme} requirements")

        for command in reqs.command_requirements(self.requirements, python=env_python):
            runcommand.run_command(command, show_trace=True, dry_run=self.dry_run)

        if reqs.requirements_need_pip(self.requirements):
            runcommand.run_command(
                [env_python, "-m", "pip", "install"]
                + reqs.pip_requirements(self.requirements, self.basename),
                show_trace=True,
                dry_run=self.dry_run,
            )

        self.progress("Done.")
        if not self.dry_run:
            self.progress(
                f"To use your virtual environment: 'source activate {self.env_name}'."
            )

    def remove(self):
        """Remove this environment."""
        self.progress(f"Removing {self.env_description}")

        if not self.env_exists():
            self.progress(f"Good news!  There is no {self.env_description}.")
            return

        conda_command = [CONDA, "env", "remove"]
        if self.force:
            conda_command.append("--yes")
        runcommand.run_command(
            conda_command + ["-n", self.env_name], show_trace=True, dry_run=self.dry_run
        )
        self.progress("Done.")
