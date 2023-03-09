"""Provide base class for modeling virtual environments."""

import os
import os.path
import sys

from .. import const, fmt, reqs, runcommand

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
            for attr, command in [
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
