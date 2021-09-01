"""Model different sorts of requirements."""

import os.path
import sys

from . import const, exceptions, runcommand

REQUIREMENTS_VENV = ["pip", "setuptools", "wheel"]

REQUIREMENTS_PLAIN = "requirements.txt"
REQUIREMENTS_DEV = os.path.join("dev", "requirements_dev.txt")
REQUIREMENTS_TEST = os.path.join("dev", "requirements_test.txt")
REQUIREMENTS_FROZEN = "requirements_frozen.txt"
REQUIREMENTS_BUILD = os.path.join("dev", "requirements_build.txt")
REQUIREMENTS_PACKAGE = "{basename}"
REQUIREMENTS_SOURCE = ["{python}", "setup.py", "install"]

REQ_SCHEME_PLAIN = "plain"
REQ_SCHEME_DEV = "dev"
REQ_SCHEME_FROZEN = "frozen"
REQ_SCHEME_PACKAGE = "package"
REQ_SCHEME_SOURCE = "source"
REQ_SCHEME_VENV = "venv"

DEV_REQ_SCHEMES = {
    REQ_SCHEME_DEV,
}

ALL_REQ_SCHEMES = [
    REQ_SCHEME_PLAIN,
    REQ_SCHEME_DEV,
    REQ_SCHEME_FROZEN,
    REQ_SCHEME_PACKAGE,
    REQ_SCHEME_SOURCE,
]

########################################

REQUIREMENTS = {
    REQ_SCHEME_PLAIN: {
        const.FROM_FILES: [REQUIREMENTS_PLAIN],
    },
    REQ_SCHEME_DEV: {
        const.FROM_FILES: [
            REQUIREMENTS_PLAIN,
            REQUIREMENTS_BUILD,
            REQUIREMENTS_DEV,
            REQUIREMENTS_TEST,
        ],
    },
    REQ_SCHEME_FROZEN: {
        const.FROM_FILES: [REQUIREMENTS_FROZEN],
    },
    REQ_SCHEME_PACKAGE: {
        const.FROM_PACKAGES: [REQUIREMENTS_PACKAGE],
    },
    REQ_SCHEME_SOURCE: {
        const.FROM_COMMANDS: [REQUIREMENTS_SOURCE],
    },
}


def requirements_for_venv():
    """Get the requirements specific to Python venvs."""
    return REQUIREMENTS_VENV


def requirements_sources_for_scheme(req_scheme):
    """Get the lists of requirements for the given requirements scheme."""
    return REQUIREMENTS[req_scheme]


def check_requirements_for_scheme(req_scheme):
    """Check the requirements sources for `req_scheme` for missing ones."""
    missing = []
    for requirements_file in requirements_sources_for_scheme(req_scheme).get(
        const.FROM_FILES, []
    ):
        if not os.path.exists(requirements_file):
            missing.append(requirements_file)
    if missing:
        noun = "file" if len(missing) == 1 else "files"
        raise exceptions.MissingRequirementsError(
            f"Missing requirements {noun}", missing
        )


def any_requirements_from(requirements, whence):
    """Tell whether `requirements` has a ``FROM_*`` key in `whence`."""
    return set(requirements) & whence  # set intersection


def requirements_need_pip(requirements):
    """Tell whether `requirements` has a ``FROM_*`` key that needs ``pip``."""
    return any_requirements_from(requirements, {const.FROM_FILES, const.FROM_PACKAGES})


def command_requirements(requirements, **kwargs):
    """Get any non-``pip`` commands from `requirements`."""
    commands = []
    for command in requirements.get(const.FROM_COMMANDS, []):
        commands.append([x.format(**kwargs) for x in command])
    return commands


def pip_requirements(requirements, basename):
    """Get the full list of ``pip`` arguments needed from `requirements`."""
    pip_arguments = []
    for a_file in requirements.get(const.FROM_FILES, []):
        pip_arguments.append("-r")
        pip_arguments.append(a_file)
    for package_spec in requirements.get(const.FROM_PACKAGES, []):
        pip_arguments.append(package_spec.format(basename=basename))
    return pip_arguments


########################################


REQUIREMENTS_NEW = {
    REQ_SCHEME_PLAIN: [
        {const.FROM_FILES: [REQUIREMENTS_PLAIN]},
    ],
    REQ_SCHEME_DEV: [
        {
            const.FROM_FILES: [
                REQUIREMENTS_PLAIN,
                REQUIREMENTS_BUILD,
                REQUIREMENTS_DEV,
                REQUIREMENTS_TEST,
            ],
        },
    ],
    REQ_SCHEME_FROZEN: [
        {const.FROM_FILES: [REQUIREMENTS_FROZEN]},
    ],
    REQ_SCHEME_PACKAGE: [
        {const.FROM_PACKAGES: [REQUIREMENTS_PACKAGE]},
    ],
    REQ_SCHEME_SOURCE: [
        {const.FROM_COMMANDS: [REQUIREMENTS_SOURCE]},
    ],
    REQ_SCHEME_VENV: [
        {const.FROM_PACKAGES: REQUIREMENTS_VENV},
    ],
}


class ReqScheme(object):
    """
    Model a requirements scheme.

    :Args:
        scheme
            The name of the requirements scheme to use; one of ``REQ_SCHEME_*``

        python
            (optional) The path to the Python interpreter to use for these
            requirements; this should generally be the one in the virtual
            environment the requirements are to be installed in.  May be set
            later using `~python_venv.reqs.ReqScheme.use_python()`:py:meth:.

        basename
            (optional) The basename of the Python package to install if using a
            package-based scheme.

        dry_run
            (optional) If `True`-ish, run commands in dry-run mode.

        show_trace
            (optional) If `True`-ish, show what commands are being run.

        env
            (optional) A replacement for `os.environ`:py:attr: to use when
            running commands (important for Python virtual environments).

        stdout
            (optional) A replacement for `sys.stdout`:py:attr: to use when
            running commands.  Rarely needed.

        stderr
            (optional) A replacement for `sys.stderr`:py:attr: to use when
            running commands.  Rarely needed.
    """

    def __init__(
        self,
        scheme,
        python=None,
        basename=None,
        dry_run=False,
        show_trace=True,
        env=None,
        stdout=None,
        stderr=None,
    ):
        self.scheme = scheme
        self.python = python
        self.basename = basename
        self.dry_run = bool(dry_run)
        self.show_trace = bool(show_trace)
        self.env = env
        self.stdout = sys.stdout if stdout is None else stdout
        self.stderr = sys.stderr if stderr is None else stderr
        self.requirements = self._get_requirements(self.scheme)
        self._set_pip_install_command()

    def _get_requirements(self, scheme):
        scheme = scheme if scheme else self.scheme
        return REQUIREMENTS_NEW[scheme]

    def use_python(self, python):
        """Set the path to the Python interpreter to use."""
        self.python = python
        self._set_pip_install_command()

    def _set_pip_install_command(self):
        self.pip_install_command = [self.python, "-m", "pip", "install"]

    def is_dev(self):
        """Tell whether this is a development requirements scheme."""
        return self.scheme in DEV_REQ_SCHEMES

    def _replace(self, strings):
        replacements = {
            "python": self.python,
            "basename": self.basename,
        }
        return [x.format(**replacements) for x in strings]

    def fulfill(self, upgrade=False):
        """Fulfill the requirements specified in the scheme."""
        for entry in self.requirements:
            for (whence, sources) in entry.items():
                if whence == const.FROM_FILES:
                    self._fulfill_files(sources, upgrade=upgrade)
                elif whence == const.FROM_PACKAGES:
                    self._fulfill_packages(sources, upgrade=upgrade)
                elif whence == const.FROM_COMMANDS:
                    self._fulfill_commands(sources)
                else:
                    raise IndexError(f"Unhandled requirement source: {whence}")

    def _fulfill_pip_requirements(self, pip_arguments, upgrade):
        pip_install_command = self.pip_install_command
        if upgrade:
            pip_install_command += ["--upgrade"]
        runcommand.run_command(
            pip_install_command + pip_arguments,
            show_trace=self.show_trace,
            dry_run=self.dry_run,
            env=self.env,
            stdout=self.stdout,
            stderr=self.stderr,
        )

    def _fulfill_packages(self, package_specs, upgrade):
        self._fulfill_pip_requirements(self._replace(package_specs), upgrade=upgrade)

    def _fulfill_files(self, files, upgrade):
        pip_arguments = []
        for a_file in files:
            pip_arguments.append("-r")
            pip_arguments.append(a_file)
        self._fulfill_pip_requirements(pip_arguments, upgrade=upgrade)

    def _fulfill_commands(self, commands):
        for command in commands:
            runcommand.run_command(
                self._replace(command),
                show_trace=self.show_trace,
                dry_run=self.dry_run,
                env=self.env,
                stdout=self.stdout,
                stderr=self.stderr,
            )

    def check(self):
        """Check the requirements sources for missing things."""
        missing = []
        for entry in self.requirements:
            for requirements_file in entry.get(const.FROM_FILES, []):
                if not os.path.exists(requirements_file):
                    missing.append(requirements_file)
        if missing:
            noun = "file" if len(missing) == 1 else "files"
            raise exceptions.MissingRequirementsError(
                f"Missing requirements {noun}", missing
            )
