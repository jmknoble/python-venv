"""Provide class model for virtual environments."""

import os
import os.path
import shutil
import stat
import subprocess
import sys

from . import const, exceptions, fmt, reqs, runcommand

####################


class BaseVirtualEnvironment(object):
    """
    Model an abstract base virtual environment.

    :Args:
        req_scheme
            The requirements scheme from `~python_venv.reqs`:py:mod: to use for
            this environment.

        pip_args
            (optional) Requirement specifications to pass to the ``pip``
            command if `req_scheme` is ``pip``.

        basename
            (optional) The basename of the Python project in the current
            directory (default: inferred).

        env_name
            (optional) The name of the virtual environment to create (default:
            inferred).

        env_prefix
            (optional) The path to the directory in which to create the virtual
            environment (default: inferred)

        dry_run
            (optional) If `True`-ish, say what would be done rather than doing it.

        force
            (optional) If `True`-ish, avoid any prompts.

        message_prefix
            (optional) The prefix to use when printing progress or feedback
            messages.

        python
            (optional) The basename of or path to the Python interpreter to use
            for running Python commands.

        os_environ
            (optional) If supplied, a dictionary that replaces
            `os.environ`:py:attr: when subprocesses are called.

        ignore_preflight_checks
            (optional) If `True`-ish, do not run pre-flight checks; use
            caution, as this could lead to unintended consequences!
    """

    def __init__(
        self,
        req_scheme,
        pip_args=None,
        basename=None,
        env_name=None,
        env_prefix=None,
        dry_run=False,
        force=False,
        message_prefix=None,
        python=None,
        os_environ=None,
        ignore_preflight_checks=False,
    ):
        self.req_scheme = req_scheme

        self.pip_args = [] if pip_args is None else pip_args
        self._basename = basename
        self._env_name = env_name
        self._env_prefix = env_prefix

        self.formatter = fmt.Formatter(basename=self._basename)

        self.dry_run = dry_run
        self.force = force
        self.message_prefix = message_prefix
        self.python = python
        self.os_environ = os_environ
        self.ignore_preflight_checks = ignore_preflight_checks

        self._requirements = None
        self._package_name = None
        self._env_description = None

        self._have_setup_py = None

        if self.message_prefix is None:
            self.message_prefix = const.MESSAGE_PREFIX

        if self.python is None:
            self.python = const.PYTHON

        if self.os_environ is None:
            self.os_environ = os.environ.copy()

    def progress(self, message, suffix="..."):
        """Print a progress message."""
        message_parts = [message]
        if suffix and not message.endswith("."):
            message_parts.append(suffix)
        runcommand.print_trace(
            message_parts, trace_prefix=const.MESSAGE_PREFIX, dry_run=self.dry_run
        )

    @property
    def requirements(self):
        """Get the requirements sources for this environment."""
        if self._requirements is None:
            self._requirements = reqs.ReqScheme(
                self.req_scheme,
                pip_args=self.pip_args,
                basename=self.basename,
                formatter=self.formatter,
                dry_run=self.dry_run,
                env=self.os_environ,
            )
        return self._requirements

    @property
    def have_setup_py(self):
        """Check (and cache) whether a setup.py exists."""
        if self._have_setup_py is None:
            self._have_setup_py = os.path.exists("setup.py")
        return self._have_setup_py

    @property
    def need_setup_py(self):
        """Tell whether a setup.py is necessary."""
        return self.req_scheme not in {reqs.REQ_SCHEME_PIP}

    @property
    def package_name(self):
        """Get the package name for the Python project in the current directory."""
        if not self.formatter.has("name"):
            if not self.need_setup_py and not self.have_setup_py:
                return None
            for (attr, command) in [
                ("name", [self.python, "setup.py", "--name"]),
                ("version", [self.python, "setup.py", "--version"]),
            ]:
                value = runcommand.run_command(
                    command,
                    dry_run=False,
                    return_output=True,
                    show_trace=False,
                    env=self.os_environ,
                    stderr=sys.stderr,
                )
                if value.endswith("\n"):
                    value = value[:-1]
                self.formatter.set(attr, value)
        return self.formatter.get("name")

    @property
    def basename(self):
        """Get the basename for the Python project in the current directory."""
        if self._basename is None and self.package_name is not None:
            self._basename = self.package_name.replace("_", "-")
            self.formatter.add(basename=self._basename)
        return self._basename

    @property
    def env_name(self):
        """Get the environment name (abstract method)."""
        raise NotImplementedError(
            "This is an abstract base class, please inherit from it."
        )

    @property
    def env_prefix(self):
        """Get the prefix or containing directory for the environment."""
        if self._env_prefix is None:
            return ""
        return self._env_prefix

    def have_env_prefix(self):
        """
        Tell if `~python_venv.env.BaseVirtualEnvironment.env_prefix`:py:attr: is set.
        """
        return bool(self.env_prefix)

    @property
    def env_dir(self):
        """Get the directory where this environment lives."""
        return os.path.join(self.env_prefix, self.env_name)

    @property
    def env_bin_dir(self):
        """Get the path to the ``bin`` directory in this environment."""
        try:
            self._env_bin_dir
        except AttributeError:
            self._env_bin_dir = None

        if self._env_bin_dir is None:
            self._env_bin_dir = os.path.join(self.env_dir, "bin")

        return self._env_bin_dir

    @property
    def env_python(self):
        """Get the path to the Python executable in this environment."""
        try:
            self._env_python
        except AttributeError:
            self._env_python = None

        if self._env_python is None:
            self._env_python = os.path.join(
                self.env_bin_dir, os.path.basename(self.python)
            )
        return self._env_python

    @property
    def abs_env_dir(self):
        """Get a full path to this environment."""
        return os.path.abspath(self.env_dir)

    @property
    def env_description(self):
        """Get a textual description of this environment (abstract method)."""
        raise NotImplementedError(
            "This is an abstract base class, please inherit from it."
        )

    def progress_start(self):
        """Emit a progress message when starting any activity."""
        pass

    def preflight_checks_for_create(self):
        """Run preflight checks needed before creating this environment."""
        if not self.ignore_preflight_checks:
            self.requirements.check()

    def check_preexisting(self):
        """Check for a pre-existing environment."""
        raise NotImplementedError(
            "This is an abstract base class, please inherit from it."
        )

    def suggest_activate(self):
        """Suggest how to activate the environment."""
        raise NotImplementedError(
            "This is an abstract base class, please inherit from it."
        )

    def progress_create(self):
        """Emit a progress message for creating an environment."""
        self.progress(f"Creating {self.env_description}")

    def pre_create(self):
        """Do needed things before creating the environment (abstract method)."""
        self.progress_start()
        self.progress_create()
        self.preflight_checks_for_create()
        self.check_preexisting()

    def do_create(self):
        """Do the things to create the environment (abstract method)."""
        raise NotImplementedError(
            "This is an abstract base class, please inherit from it."
        )

    def post_create(self):
        """Do needed things after creating the environment (abstract method)."""
        self.progress("Done.")
        self.suggest_activate()

    def create(self):
        """Create the environment (abstract method)."""
        self.pre_create()
        self.do_create()
        self.post_create()

    def progress_remove(self):
        """Emit a progress message for removing an environment."""
        self.progress(f"Removing {self.env_description}")

    def pre_remove(self):
        """Do needed things before removing the environment (abstract method)."""
        self.progress_start()
        self.progress_remove()

    def do_remove(self):
        """Do the things to remove the environment (abstract method)."""
        raise NotImplementedError(
            "This is an abstract base class, please inherit from it."
        )

    def post_remove(self):
        """Do needed things after removing the environment (abstract method)."""
        self.progress("Done.")

    def remove(self):
        """Remove the environment (abstract method)."""
        self.pre_remove()
        self.do_remove()
        self.post_remove()

    def progress_replace(self):
        """Emit a progress message for replacing an environment."""
        self.progress(f"Replacing {self.env_description}")

    def pre_replace(self):
        """Do needed things before replacing the environment (abstract method)."""
        self.progress_start()
        self.progress_replace()
        self.preflight_checks_for_create()

    def do_replace(self):
        """Do the things to replace the environment (abstract method)."""
        self.progress_remove()
        self.do_remove()
        self.progress_create()
        self.do_create()

    def post_replace(self):
        """Do needed things after replacing the environment (abstract method)."""
        self.post_create()

    def replace(self):
        """Replace this environment (remove, then create it)."""
        self.pre_replace()
        self.do_replace()
        self.post_replace()


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