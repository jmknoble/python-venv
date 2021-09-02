"""Provide package constants."""

STATUS_SUCCESS = 0
STATUS_FAILURE = 1
STATUS_HELP = 2

PYTHON = "python3"
PYTHON_VERSION_REGEX = r"^[0-9]+(\.[0-9]+){0,2}"  # Must start with X, X.Y, or X.Y.Z

CONDA = "conda"
VENV_DIR = ".venv"
DEV_SUFFIX = "-dev"

MESSAGE_PREFIX = "==> "

ENV_TYPE_VENV = "venv"
ENV_TYPE_CONDA = "conda"

ENV_TYPES = [
    ENV_TYPE_VENV,
    ENV_TYPE_CONDA,
]

FROM_FILES = "files"
FROM_PACKAGES = "packages"
FROM_COMMANDS = "commands"
FROM_BDIST_WHEEL = "bdist_wheel"
FROM_PIP_ARGS = "pip_args"
