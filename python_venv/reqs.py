"""Model different sorts of requirements."""

import os.path

from . import exceptions

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

FROM_FILES = "files"
FROM_PACKAGES = "packages"
FROM_COMMANDS = "commands"

REQUIREMENTS = {
    REQ_SCHEME_PLAIN: {
        FROM_FILES: [REQUIREMENTS_PLAIN],
    },
    REQ_SCHEME_DEV: {
        FROM_FILES: [
            REQUIREMENTS_PLAIN,
            REQUIREMENTS_BUILD,
            REQUIREMENTS_DEV,
            REQUIREMENTS_TEST,
        ],
    },
    REQ_SCHEME_FROZEN: {
        FROM_FILES: [REQUIREMENTS_FROZEN],
    },
    REQ_SCHEME_PACKAGE: {
        FROM_PACKAGES: [REQUIREMENTS_PACKAGE],
    },
    REQ_SCHEME_SOURCE: {
        FROM_COMMANDS: [REQUIREMENTS_SOURCE],
    },
}


def is_dev_req_scheme(req_scheme):
    """Tell whether `req_scheme` is a development requirements scheme."""
    return req_scheme in DEV_REQ_SCHEMES


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
        FROM_FILES, []
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
    return any_requirements_from(requirements, {FROM_FILES, FROM_PACKAGES})


def command_requirements(requirements, **kwargs):
    """Get any non-``pip`` commands from `requirements`."""
    commands = []
    for command in requirements.get(FROM_COMMANDS, []):
        commands.append([x.format(**kwargs) for x in command])
    return commands


def pip_requirements(requirements, basename):
    """Get the full list of ``pip`` arguments needed from `requirements`."""
    pip_arguments = []
    for a_file in requirements.get(FROM_FILES, []):
        pip_arguments.append("-r")
        pip_arguments.append(a_file)
    for package_spec in requirements.get(FROM_PACKAGES, []):
        pip_arguments.append(package_spec.format(basename=basename))
    return pip_arguments
