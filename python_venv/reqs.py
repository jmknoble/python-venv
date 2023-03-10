"""Model different sorts of requirements."""

import os.path
import re
import sys

from . import const, exceptions, fmt, runcommand

REQUIREMENTS_PLAIN = "requirements.txt"
REQUIREMENTS_DEV = "requirements_dev.txt"
REQUIREMENTS_DEVPLUS = os.path.join("dev", "requirements_dev.txt")
REQUIREMENTS_TEST = os.path.join("dev", "requirements_test.txt")
REQUIREMENTS_FROZEN = "requirements_frozen.txt"
REQUIREMENTS_BUILD = os.path.join("dev", "requirements_build.txt")

REQUIREMENTS_PIP = True
REQUIREMENTS_PACKAGE = "{basename}"

REQUIREMENTS_SOURCE = ["{python}", "setup.py", "install"]

# https://pypa-build.readthedocs.io/en/stable/index.html
REQUIREMENTS_BDIST_WHEEL = ["{python}", "-m", "build", "--outdir", const.DIST_DIR]
REQUIREMENTS_WHEELFILE = "{wheelfile}"

REQUIREMENTS_VENV = ["pip", "setuptools", "wheel"]
REQUIREMENTS_VENV_WHEEL = ["build"]

REQ_SCHEME_PLAIN = "plain"
REQ_SCHEME_DEV = "dev"
REQ_SCHEME_DEVPLUS = "devplus"
REQ_SCHEME_FROZEN = "frozen"
REQ_SCHEME_PACKAGE = "package"
REQ_SCHEME_PIP = "pip"
REQ_SCHEME_SOURCE = "source"
REQ_SCHEME_WHEEL = "wheel"
REQ_SCHEME_VENV = "venv"

DEV_REQ_SCHEMES = {
    REQ_SCHEME_DEV,
    REQ_SCHEME_DEVPLUS,
}

ALL_REQ_SCHEMES = [
    REQ_SCHEME_PLAIN,
    REQ_SCHEME_DEV,
    REQ_SCHEME_DEVPLUS,
    REQ_SCHEME_FROZEN,
    REQ_SCHEME_PACKAGE,
    REQ_SCHEME_PIP,
    REQ_SCHEME_SOURCE,
    REQ_SCHEME_WHEEL,
]

REQUIREMENTS = {
    REQ_SCHEME_PLAIN: [
        {const.FROM_FILES: [REQUIREMENTS_PLAIN]},
    ],
    REQ_SCHEME_DEV: [
        {const.FROM_FILES: [REQUIREMENTS_DEV]},
    ],
    REQ_SCHEME_DEVPLUS: [
        {
            const.FROM_FILES: [
                REQUIREMENTS_PLAIN,
                REQUIREMENTS_BUILD,
                REQUIREMENTS_DEVPLUS,
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
    REQ_SCHEME_PIP: [
        {const.FROM_PIP_ARGS: REQUIREMENTS_PIP},
    ],
    REQ_SCHEME_SOURCE: [
        {const.FROM_COMMANDS: [REQUIREMENTS_SOURCE]},
    ],
    REQ_SCHEME_WHEEL: [
        {const.FROM_BDIST_WHEEL: REQUIREMENTS_BDIST_WHEEL},
        {const.FROM_PACKAGES: [REQUIREMENTS_WHEELFILE]},
    ],
}

SPECIAL_REQUIREMENTS = {
    REQ_SCHEME_VENV: {
        "default": [
            {const.FROM_PACKAGES: REQUIREMENTS_VENV},
        ],
        REQ_SCHEME_WHEEL: [
            {const.FROM_PACKAGES: REQUIREMENTS_VENV + REQUIREMENTS_VENV_WHEEL},
        ],
    }
}

REGEX_BDIST_WHEEL_WHEELFILE = (
    r"(?im)^Successfully built [^ ]+ and (?P<wheelfile>.*\.whl)"
)


class ReqScheme(object):
    """
    Model a requirements scheme.

    :Args:
        scheme
            The name of the requirements scheme to use; one of ``REQ_SCHEME_*``

        pip_args
            (optional) Requirement specifications to pass to ``pip`` if
            `scheme` is `REQ_SCHEME_PIP`:py:const:.

        python
            (optional) The path to the Python interpreter to use for these
            requirements; this should generally be the one in the virtual
            environment the requirements are to be installed in.  May be set
            later using `~python_venv.reqs.ReqScheme.use_python()`:py:meth:.

        basename
            (optional) The basename of the Python package to install if using a
            package-based scheme.

        formatter
            (optional) A `~python_venv.fmt.Formatter()`:py:class: object to
            use for string template formatting; if not supplied, one is
            created and populated with any supplied values for `python` and
            `basename`.

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
        pip_args=None,
        python=None,
        basename=None,
        formatter=None,
        dry_run=False,
        show_trace=True,
        env=None,
        stdout=None,
        stderr=None,
        supplemental_scheme=None,
    ):
        self.scheme = scheme
        self.pip_args = [] if pip_args is None else pip_args
        self.python = python
        self.basename = basename
        self.formatter = formatter
        self.dry_run = bool(dry_run)
        self.show_trace = bool(show_trace)
        self.env = env
        self.stdout = sys.stdout if stdout is None else stdout
        self.stderr = sys.stderr if stderr is None else stderr
        self.supplemental_scheme = supplemental_scheme

        if self.formatter is None:
            self.formatter = fmt.Formatter(python=self.python, basename=self.basename)

        self._handled_requirements_sources = set()

        self.requirements = self._get_requirements()
        self._set_pip_install_command()

    def _get_requirements(self):
        # TODO: Turn this into an @property
        special = SPECIAL_REQUIREMENTS.get(self.scheme, None)
        if special:
            default = special.get("default", None)
            special = (
                special.get(self.supplemental_scheme, default)
                if self.supplemental_scheme
                else default
            )
        found = REQUIREMENTS.get(self.scheme, special)
        if found is None:
            raise KeyError(self.scheme)
        return list(found)

    def is_dev(self):
        """Tell whether this is a development requirements scheme."""
        return self.scheme in DEV_REQ_SCHEMES

    def use_python(self, python):
        """Set the path to the Python interpreter to use."""
        # TODO: Turn this into an @property
        self.python = python
        self.formatter.add(python=python)
        self._set_pip_install_command()

    def _set_pip_install_command(self):
        self.pip_install_command = (
            None if self.python is None else [self.python, "-m", "pip", "install"]
        )

    def _format(self, strings):
        return self.formatter.format(strings)

    def _pip_argify_files(self, files):
        pip_arguments = []
        for a_file in files:
            pip_arguments.append("-r")
            pip_arguments.append(a_file)
        return pip_arguments

    def _get_requirements_files(self, entry):
        return entry.get(const.FROM_FILES, [])

    def _get_requirements_packages(self, entry):
        return self._format(entry.get(const.FROM_PACKAGES, []))

    def _get_requirements_pip_args(self, entry):
        if entry.get(const.FROM_PIP_ARGS, False):
            return self._format(self.pip_args)
        return []

    def _get_requirements_commands(self, entry):
        return [self._format(x) for x in entry.get(const.FROM_COMMANDS, [])]

    def _get_requirements_bdist_wheel(self, entry):
        return self._format(entry.get(const.FROM_BDIST_WHEEL, []))

    def _collect_pip_arguments(self, entry):
        pip_arguments = self._pip_argify_files(self._get_requirements_files(entry))
        pip_arguments.extend(self._get_requirements_packages(entry))
        pip_arguments.extend(self._get_requirements_pip_args(entry))
        self._handled_requirements_sources.add(const.FROM_FILES)
        self._handled_requirements_sources.add(const.FROM_PACKAGES)
        self._handled_requirements_sources.add(const.FROM_PIP_ARGS)
        return pip_arguments

    def _collect_commands(self, entry):
        self._handled_requirements_sources.add(const.FROM_COMMANDS)
        return self._get_requirements_commands(entry)

    def _collect_bdist_wheel(self, entry):
        self._handled_requirements_sources.add(const.FROM_BDIST_WHEEL)
        return self._get_requirements_bdist_wheel(entry)

    def fulfill(self, upgrade=False):
        """Fulfill the requirements specified in the scheme."""
        for entry in self.requirements:
            pip_arguments = self._collect_pip_arguments(entry)
            commands = self._collect_commands(entry)
            bdist_wheel = self._collect_bdist_wheel(entry)
            if pip_arguments:
                self._fulfill_pip_requirements(pip_arguments, upgrade=upgrade)
            if commands:
                self._fulfill_commands(commands)
            if bdist_wheel:
                self._fulfill_bdist_wheel(bdist_wheel)
            for whence in entry:
                if whence not in self._handled_requirements_sources:
                    raise IndexError(f"Unhandled requirement source: {whence}")

    def _fulfill_pip_requirements(self, pip_arguments, upgrade):
        pip_install_command = self.pip_install_command
        if upgrade:
            pip_install_command.append("--upgrade")
        pip_install_command.extend(pip_arguments)
        runcommand.run_command(
            pip_install_command,
            show_trace=self.show_trace,
            dry_run=self.dry_run,
            env=self.env,
            stdout=self.stdout,
            stderr=self.stderr,
        )

    def _fulfill_commands(self, commands):
        for command in commands:
            runcommand.run_command(
                command,
                show_trace=self.show_trace,
                dry_run=self.dry_run,
                env=self.env,
                stdout=self.stdout,
                stderr=self.stderr,
            )

    def _fulfill_bdist_wheel(self, bdist_wheel_command):
        output = runcommand.run_command(
            bdist_wheel_command,
            show_trace=self.show_trace,
            dry_run=self.dry_run,
            return_output=True,
            env=self.env,
        )
        if self.dry_run:
            wheelfile = self._format("{name}-{version}-*.whl")
        else:
            match = re.search(REGEX_BDIST_WHEEL_WHEELFILE, output)
            if not match:
                raise RuntimeError(f"unable to detect wheelfile: {bdist_wheel_command}")
            wheelfile = match.group("wheelfile")
        wheelfile = os.path.join(const.DIST_DIR, wheelfile)
        self.formatter.add(wheelfile=wheelfile)

    def check(self):
        """Check the requirements sources for missing things."""
        missing = []
        for entry in self.requirements:
            for requirements_file in self._get_requirements_files(entry):
                if not os.path.exists(requirements_file):
                    missing.append(requirements_file)
        if missing:
            noun = "file" if len(missing) == 1 else "files"
            raise exceptions.MissingRequirementsError(
                f"Missing requirements {noun}", missing
            )
